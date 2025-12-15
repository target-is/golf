from odoo import models, fields, api
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = "stock.picking"

    has_sale_access = fields.Boolean(compute="_compute_has_sale_access")

    def _compute_has_sale_access(self):
        user = self.env.user
        for rec in self:
            rec.has_sale_access = user.has_group('sales_team.group_sale_salesman')

    is_cr_receipt = fields.Boolean(
        compute="_compute_is_cr_receipt",
        store=False
    )

    def _compute_is_cr_receipt(self):
        for rec in self:
            rec.is_cr_receipt = bool(
                rec.picking_type_id and
                rec.picking_type_id.code == "incoming" and
                rec.picking_type_id.is_component_receiving_enabled
            )

    cr_state = fields.Selection([
        ("draft", "Draft"),
        ("waiting_ro", "Waiting Create RO"),
        ("ro_created", "RO Created"),
        ("cancel", "Cancelled"),  # ← NEW
    ], default="draft")

    # =====================================================
    # Find Picking Type based on service category
    # =====================================================
    def _find_picking_type_for_service(self, service_category):
        if not service_category:
            return False

        PickingType = self.env['stock.picking.type']

        picking_type = PickingType.search([
            ('select_service', '=', service_category)
        ], limit=1)

        return picking_type

    # =====================================================
    # Create Repair Orders for each operation line
    # =====================================================
    def _create_repair_orders(self):
        Repair = self.env["repair.order"]
        Move = self.env["stock.move"].with_context(from_backend=True)  # ← أهم تعديل

        for move in self.move_ids:

            # Tag
            tag = self._get_tag_from_service_category(move.service_category)

            picking_type = self._find_picking_type_for_service(move.service_category)
            if not picking_type or not picking_type.sequence_id:
                raise ValidationError(
                    f"No sequence defined on Picking Type for service category: {move.service_category}"
                )
            # Create Repair Order
            ro = Repair.create({
                "product_id": move.product_id.id,
                "partner_id": self.partner_id.id,
                "location_id": self.location_id.id,
                "location_dest_id": self.location_dest_id.id,
                "picking_id": self.id,

                # ⭐ أهم إضافة بناءً على طلبك
                "picking_type_id": picking_type.id if picking_type else False,

                "product_qty": move.quantity,
            })
            # Apply tag
            if tag:
                ro.write({"tag_ids": [(4, tag.id)]})

            # Spare Parts Lines
            spare_lines = move.product_id.product_tmpl_id.spareparts_line_ids

            for spare in spare_lines:
                Move.create({
                    "repair_id": ro.id,
                    "repair_line_type": "add",

                    "product_id": spare.spare_product_id.id,

                    # ← أهم جزئية:
                    "product_uom_qty": move.product_uom_qty,  # Demand
                    "quantity": move.quantity,  # Quantity Done

                    "product_uom": spare.spare_product_id.uom_id.id,
                    "location_id": self.location_id.id,
                    "location_dest_id": self.location_dest_id.id,
                    "company_id": self.company_id.id,
                    "partner_id": self.partner_id.id,
                })

        self.message_post(body="✔ Repair Orders created and Spare Parts added automatically.")

    # =====================================================
    # Create REAL Activities for Sales
    # =====================================================
    def _assign_sales_activities(self):
        self.ensure_one()
        _logger.info("📌 Assign Sales Activities for Picking: %s", self.name)

        # كل جروبات الـ Sales
        sales_groups_xmlids = [
            "sales_team.group_sale_salesman",  # Own Documents Only
            "sales_team.group_sale_salesman_all_leads",  # All Documents
            "sales_team.group_sale_manager",  # Sales Administrator
        ]

        # تحويل XMLIDs → IDs
        sales_group_ids = []
        for xmlid in sales_groups_xmlids:
            try:
                gid = self.env.ref(xmlid).id
                sales_group_ids.append(gid)
                _logger.info("📌 Added Sales Group: %s = %s", xmlid, gid)
            except:
                _logger.warning("⚠️ Group not found: %s", xmlid)

        if not sales_group_ids:
            _logger.warning("⚠️ No Sales groups found at all!")
            return

        # البحث عن المستخدمين اللي داخل أي جروب من دول
        self.env.cr.execute("""
            SELECT DISTINCT uid 
            FROM res_groups_users_rel 
            WHERE gid IN %s
        """, (tuple(sales_group_ids),))

        user_ids = [row[0] for row in self.env.cr.fetchall()]
        _logger.info("📌 Raw Sales Users IDs: %s", user_ids)

        if not user_ids:
            _logger.warning("⚠️ No Sales users assigned to any Sales group!")
            return

        users = self.env["res.users"].browse(user_ids)

        # ================================
        # 🚫 استبعاد OdooBot + Root User
        # ================================
        exclude_ids = []
        for bot in ["base.user_odoo_bot", "base.user_root"]:
            try:
                exclude_ids.append(self.env.ref(bot).id)
            except:
                pass

        users = users.filtered(lambda u: u.id not in exclude_ids)

        _logger.info("📌 Final Sales Users (after filtering bot/root): %s", users.ids)

        if not users:
            _logger.warning("⚠️ No valid Sales users left after filtering!")
            return

        # إنشاء Activity
        Activity = self.env['mail.activity']
        activity_type = self.env.ref("mail.mail_activity_data_todo")

        for user in users:
            Activity.create({
                "res_id": self.id,
                "res_model_id": self.env.ref("stock.model_stock_picking").id,
                "activity_type_id": activity_type.id,
                "summary": "Waiting Create RO",
                "user_id": user.id,
                "note": """
                    👋 <b>Dear Sales Team,</b><br/><br/>

                    A Component Receipt has been completed and requires your action.<br/>
                    Please review the received items and proceed with creating the required Repair Order.<br/><br/>

                    📌 <b>Picking:</b> %s <br/><br/>

                    Thank you for your prompt attention.
                """ % (self.name),

            })
            _logger.info("✔ Activity Created for Sales User: %s", user.name)

    # =====================================================
    # Wizard 1 Button
    # =====================================================
    def action_open_cr_ro_decision(self):
        return {
            "type": "ir.actions.act_window",
            "name": "Repair Order Received?",
            "res_model": "cr.repair.decision.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"active_id": self.id},
        }


    # =====================================================
    # Wizard 2 Button
    # =====================================================
    def action_open_create_ro_wizard(self):
        return {
            "type": "ir.actions.act_window",
            "name": "Create RO",
            "res_model": "cr.create.ro.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"active_id": self.id},
        }

    # =====================================================
    # create notification
    # =====================================================
    def _notify_ro_created(self):
        message = f"Repair Orders have been created for picking '{self.name}'."

        self.env['bus.bus']._sendone(
            self.env.user.partner_id,
            'simple_notification',
            {
                'message': message,
                'type': 'success',  # أخضر
                'sticky': False,
            }
        )

    def _get_tag_from_service_category(self, category_value):
        """Create or fetch tag using FULL Service Category label."""
        if not category_value:
            return False

        Move = self.env['stock.move']

        # Get selection list safely across all Odoo versions
        selection = Move._fields['service_category']._description_selection(self.env)

        # Convert value → label
        label = dict(selection).get(category_value, category_value)

        Tag = self.env["repair.tags"]

        # Search by full label
        tag = Tag.search([("name", "=", label)], limit=1)

        if not tag:
            tag = Tag.create({"name": label})

        return tag

    def copy(self, default=None):
        default = dict(default or {})
        # Reset CR state for returned pickings
        default['cr_state'] = 'draft'
        return super().copy(default)


# ==========================================================
# Wizard 1 — YES / NO
# ==========================================================
class CRRepairDecisionWizard(models.TransientModel):
    _name = "cr.repair.decision.wizard"
    _description = "CR — YES/NO Wizard"

    option = fields.Selection([
        ("yes", "Repair Order Received — YES"),
        ("no", "Repair Order Received — NO"),
    ], required=True)

    def action_confirm(self):
        picking = self.env["stock.picking"].browse(self.env.context.get("active_id"))

        if self.option == "yes":
            picking._create_repair_orders()
            picking.write({'cr_state': 'ro_created'})
            picking._notify_ro_created()
            # ✔ Log Note واضحة
            picking.message_post(body="""
                     ✔ Repair Orders Created Automatically
                     System generated the Repair Order because the Component Receipt was confirmed as received.
                 """)

        else:
            picking.write({'cr_state': 'waiting_ro'})
            picking._assign_sales_activities()
            # ✔ Log note تشرح المطلوب
            picking.message_post(body="""
                      ⚠ Repair Order Not Received Yet
                      Component Receipt moved to Waiting Create RO
                      Sales Team is required to create the Repair Order manually.
                  """)
        return True



# ==========================================================
# Wizard 2 — Create RO / Cancel (Sales ONLY)
# ==========================================================
class CRCreateROWizard(models.TransientModel):
    _name = "cr.create.ro.wizard"
    _description = "CR — Create RO Wizard"

    option = fields.Selection([
        ("create", "Create Repair Orders"),
        ("cancel", "Cancel Component Receipt"),
    ], required=True)

    def action_confirm(self):
        # VALIDATION: Only Sales allowed
        if not self.env.user.has_group("sales_team.group_sale_salesman"):
            raise ValidationError("❌ Only the Sales Team can perform this action.")

        picking = self.env["stock.picking"].browse(self.env.context.get("active_id"))

        if self.option == "create":
            picking._create_repair_orders()
            picking.write({"cr_state": "ro_created"})
            picking._notify_ro_created()  # ← NEW
            picking.message_post(body=f"""
                          ✔ Repair Orders Created by Sales Team
                          User {self.env.user.name} created the Repair Orders manually from the Waiting Stage.
                      """)

        else:
            picking.write({"cr_state": "cancel"})  # ← بدل action_cancel
            picking.message_post(body=f"""
                           ❌ Component Receipt Cancelled
                           Action performed by user {self.env.user.name}.
                       """)
        return True
