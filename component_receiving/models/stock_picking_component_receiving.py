from odoo import models, fields, api
from odoo.exceptions import ValidationError


# -------------------------------------------------------------
# Stock Picking Extension — CR Operation Type + Visibility Logic
# -------------------------------------------------------------
class StockPicking(models.Model):
    _inherit = 'stock.picking'

    # يظهر فقط داخل شاشة Component Receiving
    cr_operation_type_id = fields.Many2one(
        'stock.picking.type',
        string="CR Operation Type",
        required=1,
        domain="[('id', 'in', allowed_cr_picking_type_ids)]"
    )

    # قائمة العمليات المسموح بها داخل CR فقط
    allowed_cr_picking_type_ids = fields.Many2many(
        'stock.picking.type',
        compute="_compute_allowed_cr_types",
        store=False
    )

    # هل شاشة Component Receiving؟ (تتحكم في الإظهار)
    is_cr_view = fields.Boolean(
        compute="_compute_is_cr_view",
        store=False
    )

    # ---------------------------------------------------------
    # Determine if screen is Component Receiving View
    # ---------------------------------------------------------
    def _compute_is_cr_view(self):
        for rec in self:
            rec.is_cr_view = bool(rec._context.get("is_component_receipt", False))

    # ---------------------------------------------------------
    # Allowed operation types ONLY inside CR view
    # ---------------------------------------------------------
    @api.depends('picking_type_id')
    def _compute_allowed_cr_types(self):
        Type = self.env['stock.picking.type']

        for rec in self:
            if rec._context.get("is_component_receipt", False):
                rec.allowed_cr_picking_type_ids = Type.search([
                    ('is_component_receiving_enabled', '=', True)
                ])
            else:
                rec.allowed_cr_picking_type_ids = Type.search([])

    # ---------------------------------------------------------
    # Sync CR Operation Type → picking_type_id
    # ---------------------------------------------------------
    @api.onchange('cr_operation_type_id')
    def _onchange_cr_op(self):
        if self.is_cr_view and self.cr_operation_type_id:
            self.picking_type_id = self.cr_operation_type_id

    # ---------------------------------------------------------
    # CREATE Override
    # ---------------------------------------------------------
    @api.model
    def create(self, vals):
        # لو Odoo أرسل list بدل dict
        if isinstance(vals, list):
            new_vals_list = []
            for v in vals:
                processed = v.copy()

                # REQUIRED ONLY IN COMPONENT RECEIPT
                if processed.get("is_component_receipt") and not processed.get("cr_operation_type_id"):
                    raise ValidationError("CR Operation Type is required in Component Receiving!")

                if processed.get('cr_operation_type_id'):
                    processed['picking_type_id'] = processed['cr_operation_type_id']

                if not processed.get('picking_type_id'):
                    processed['picking_type_id'] = self.env.ref('stock.picking_type_in').id

                new_vals_list.append(processed)

            return super().create(new_vals_list)

        # الحالة الطبيعية dict
        vals = vals.copy()

        # REQUIRED ONLY IN COMPONENT RECEIPT
        if vals.get("is_component_receipt") and not vals.get("cr_operation_type_id"):
            raise ValidationError("CR Operation Type is required in Component Receiving!")

        if vals.get('cr_operation_type_id'):
            vals['picking_type_id'] = vals['cr_operation_type_id']

        if not vals.get('picking_type_id'):
            vals['picking_type_id'] = self.env.ref('stock.picking_type_in').id

        return super().create(vals)

    # ---------------------------------------------------------
    # WRITE Override
    # ---------------------------------------------------------
    def write(self, vals):
        for rec in self:

            # REQUIRED ONLY IN COMPONENT RECEIPT
            if rec.is_cr_view:
                if 'cr_operation_type_id' in vals:
                    # لازم لو غير الفيلد يكون مش فاضي
                    if not vals.get("cr_operation_type_id"):
                        raise ValidationError("CR Operation Type is required in Component Receiving!")

                # لو ولا الفاليوز ولا السجل فيه قيمة
                if 'cr_operation_type_id' not in vals and not rec.cr_operation_type_id:
                    raise ValidationError("CR Operation Type is required in Component Receiving!")

                # ممنوع تغيير picking_type_id داخل Component Receiving
                if 'picking_type_id' in vals and vals['picking_type_id'] != rec.picking_type_id.id:
                    raise ValidationError("You cannot change Operation Type inside Component Receiving.")

                # sync
                if 'cr_operation_type_id' in vals:
                    vals['picking_type_id'] = vals['cr_operation_type_id']

        return super().write(vals)
