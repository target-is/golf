from odoo import models, fields, api
from odoo.exceptions import ValidationError


class RepairApprovalLine(models.Model):
    _name = "repair.approval.line"
    _description = "Repair Approval Line"
    _order = "id desc"

    has_sales_access = fields.Boolean(compute="_compute_has_sales_access")

    def _compute_has_sales_access(self):
        user = self.env.user
        allowed = (
                user.has_group('sales_team.group_sale_salesman') or
                user.has_group('sales_team.group_sale_salesman_all_leads') or
                user.has_group('sales_team.group_sale_manager')
        )
        for rec in self:
            rec.has_sales_access = allowed

    # ===========================
    #       RELATION
    # ===========================
    repair_id = fields.Many2one(
        "repair.order",
        string="Repair Order",
        required=True,
        ondelete="cascade"
    )

    # ===========================
    #       REQUIRED FIELDS
    # ===========================
    repair_line_type = fields.Selection([
        ("add", "Add"),
        ("remove", "Remove"),
        ("other", "Other"),
    ], string="Type", required=True)

    product_id = fields.Many2one(
        "product.product",
        string="Product",
        required=True
    )

    product_uom_qty = fields.Float(
        "Demand",
        required=True,
        default=1.0

    )

    quantity = fields.Float(
        "Quantity",
        required=True
    )

    product_uom = fields.Many2one(
        "uom.uom",
        string="Unit",
        required=True
    )

    # ===========================
    #     APPROVAL STATE BADGE
    # ===========================
    approve_state = fields.Selection([
        ("draft", "Draft"),
        ("waiting", "Waiting Approval"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ], default="draft", required=True)

    badge_state = fields.Html(
        compute="_compute_badge_state",
        sanitize=False
    )

    def _compute_badge_state(self):
        for rec in self:
            if rec.approve_state == "approved":
                color = "#3CB371"  # Green
            elif rec.approve_state == "rejected":
                color = "#DC143C"  # Red
            else:
                color = "#17A2B8"  # Blue

            label = dict(self._fields["approve_state"].selection).get(rec.approve_state)

            rec.badge_state = f"""
                <span style="
                    background-color:{color};
                    color:white;
                    padding:4px 8px;
                    border-radius:6px;
                    font-size:12px;
                    font-weight:bold;">
                    {label}
                </span>
            """

    # ===========================
    #      ONCHANGE PRODUCT
    # ===========================
    @api.onchange("product_id")
    def _onchange_product_id(self):
        """Fill product_uom automatically when product changes."""
        if self.product_id:
            self.product_uom = self.product_id.uom_id.id

    def action_send_request(self):
        self.ensure_one()

        # رجع الحالة إلى waiting إذا كانت مختلفة
        if self.approve_state != "waiting":
            self.approve_state = "waiting"

        # 1) جروبات Sales
        sales_groups = [
            "sales_team.group_sale_salesman",
            "sales_team.group_sale_salesman_all_leads",
            "sales_team.group_sale_manager",
        ]

        sales_group_ids = []
        for xmlid in sales_groups:
            try:
                sales_group_ids.append(self.env.ref(xmlid).id)
            except:
                pass

        if not sales_group_ids:
            return

        # 2) Get Users via SQL
        self.env.cr.execute("""
            SELECT DISTINCT uid 
            FROM res_groups_users_rel 
            WHERE gid IN %s
        """, (tuple(sales_group_ids),))

        user_ids = [row[0] for row in self.env.cr.fetchall()]
        users = self.env["res.users"].browse(user_ids)

        # ============================
        # 🚫 استبعاد OdooBot + root
        # ============================
        exclude_ids = []
        for bot_xmlid in ["base.user_odoo_bot", "base.user_root"]:
            try:
                exclude_ids.append(self.env.ref(bot_xmlid).id)
            except:
                pass

        users = users.filtered(lambda u: u.id not in exclude_ids)

        if not users:
            return

        # 3) model ID
        model_id = self.env['ir.model']._get_id('repair.order')

        Activity = self.env["mail.activity"]
        activity_type = self.env.ref("mail.mail_activity_data_todo")

        # 4) إنشاء Activities
        for user in users:
            Activity.create({
                "res_id": self.repair_id.id,
                "res_model_id": model_id,
                "activity_type_id": activity_type.id,
                "user_id": user.id,
                "summary": "Approval Request Sent",
                "note": f"Approval needed for: {self.product_id.display_name}",
            })


        return True



    # ===========================
    #     OPEN WIZARDS
    # ===========================
    def open_approve_wizard(self):
        return {
            "type": "ir.actions.act_window",
            "name": "Approve Line",
            "res_model": "approval.move.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "active_line_id": self.id,
                "action_type": "approve",
            }
        }

    def open_reject_wizard(self):
        return {
            "type": "ir.actions.act_window",
            "name": "Reject Line",
            "res_model": "approval.move.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "active_line_id": self.id,
                "action_type": "reject",
            }
        }

    def write(self, vals):
        for rec in self:
            if rec.approve_state == "waiting":
                raise ValidationError(
                    "🚫 Editing Not Allowed\n\n"
                    "This approval line is currently under review.\n"
                    "You cannot modify it while it is in the approval process.\n\n"
                    "👉 If you need changes, please delete this line and create a new one."
                )

            if rec.approve_state == "approved":
                raise ValidationError(
                    "✅ Already Approved\n\n"
                    "This approval line has already been approved and added to the repair parts.\n"
                    "Its data is locked and cannot be modified.\n\n"
                    "👉 If you need a change, please create a new one."
                )

            if rec.approve_state == "rejected":
                raise ValidationError(
                    "❌ Line Rejected\n\n"
                    "This line was rejected.\n"
                    "Rejected records cannot be edited.\n\n"
                    "👉 Please create a new one if needed."
                )

        return super().write(vals)


class ApprovalMoveWizard(models.TransientModel):
    _name = "approval.move.wizard"
    _description = "Approve / Reject Approval Line Wizard"

    confirm_text = fields.Char(string="Message", readonly=True)
    icon_html = fields.Html(compute="_compute_icon_html", sanitize=False)
    description_html = fields.Html(compute="_compute_description_html", sanitize=False)

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)

        action = self.env.context.get("action_type")
        if action == "approve":
            res["confirm_text"] = "Are you sure you want to APPROVE this line?"
        else:
            res["confirm_text"] = "Are you sure you want to REJECT this line?"

        return res

    def action_confirm(self):
        line_id = self.env.context.get("active_line_id")
        action = self.env.context.get("action_type")

        line = self.env["repair.approval.line"].browse(line_id)

        if not line:
            raise ValidationError("Approval Line not found.")

        # تنفيذ العملية
        if action == "approve":
            line.approve_state = "approved"

            # ================
            #  ⬇ CREATE REAL PART LINE IN REPAIR ORDER
            # ================
            Move = self.env["stock.move"].with_context(from_backend=True)
            Move.create({
                "repair_id": line.repair_id.id,
                "repair_line_type": line.repair_line_type,
                "product_id": line.product_id.id,
                "product_uom_qty": line.product_uom_qty,
                "quantity": line.quantity,
                "product_uom": line.product_uom.id,
                "company_id": line.repair_id.company_id.id,
                "location_id": line.repair_id.location_id.id,
                "location_dest_id": line.repair_id.location_dest_id.id,
                "partner_id": line.repair_id.partner_id.id,
            })


        # 3) Delete approval line (روح الوسيط انتهى)
        # line.unlink()
        else:
            line.approve_state = "rejected"

        return {"type": "ir.actions.act_window_close"}

    @api.depends()
    def _compute_icon_html(self):
        for rec in self:
            action = rec.env.context.get("action_type")

            if action == "approve":
                rec.icon_html = """
                    <div style="font-size:60px; color:#28a745; margin-bottom:10px; text-align:center;">
                        <i class="fa fa-check-circle"></i>
                    </div>
                """
            else:
                rec.icon_html = """
                    <div style="font-size:60px; color:#dc3545; margin-bottom:10px; text-align:center;">
                        <i class="fa fa-times-circle"></i>
                    </div>
                """

    @api.depends()
    def _compute_description_html(self):
        for rec in self:
            rec.description_html = """
                <p style="color:#666; font-size:14px; text-align:center; margin-top:5px;">
                    This action cannot be undone. Please confirm your decision.
                </p>
            """
