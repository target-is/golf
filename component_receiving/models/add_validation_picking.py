from odoo import models, fields, api
from odoo.exceptions import ValidationError


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    # ============================================================
    # 1) Flag stored in DB → This record BELONGS to Component Receipt
    # ============================================================
    is_cr_document = fields.Boolean(
        string="Is Component Receipt Document",
        default=False
    )

    # ============================================================
    # 2) Computed flag (view logic only)
    # ============================================================
    is_component_receiving = fields.Boolean(
        compute="_compute_is_component_receiving",
        store=False
    )

    @api.depends("cr_operation_type_id")
    def _compute_is_component_receiving(self):
        """يحدد هل هذا الاستلام Component Receipt."""
        for rec in self:
            rec.is_component_receiving = bool(
                rec.cr_operation_type_id and
                rec.cr_operation_type_id.is_component_receiving_enabled
            )

    # ============================================================
    # 3) OWNER logic
    # ============================================================
    owner_id = fields.Many2one(
        'res.partner',
        string="Assign Owner",
        compute="_compute_owner_id",
        inverse="_inverse_owner_id",
        store=False
    )

    _manual_owner = fields.Many2one('res.partner')

    @api.depends('partner_id', 'cr_operation_type_id')
    def _compute_owner_id(self):
        for rec in self:
            if rec.is_component_receiving:
                rec.owner_id = rec.partner_id
            else:
                rec.owner_id = rec._manual_owner or rec.owner_id

    def _inverse_owner_id(self):
        for rec in self:
            rec._manual_owner = rec.owner_id

    # ============================================================
    # 4) VALIDATION: Owner must equal Partner
    # ============================================================
    def _validate_owner_partner_match(self):
        for rec in self:
            if rec.is_component_receiving:
                if rec.owner_id.id != rec.partner_id.id:
                    raise ValidationError(
                        "Assign Owner must match Receive From inside Component Receiving!"
                    )

    # ============================================================
    # 5) VALIDATION: Origin required
    # ============================================================
    def _validate_origin_required(self):
        for rec in self:
            if rec.is_component_receiving:
                if not rec.origin or not rec.origin.strip():
                    raise ValidationError(
                        "Source Document is required in Component Receiving!"
                    )

    # ============================================================
    # 6) CREATE override
    # ============================================================
    @api.model
    def create(self, vals_list):

        # normalize input → always a list
        if isinstance(vals_list, dict):
            vals_list = [vals_list]

        for vals in vals_list:

            # لو الشاشة الحالية هي Component Receiving
            if self._context.get("is_component_receipt"):
                vals["is_cr_document"] = True     # سجّل أن هذا record تابع CR

            # VALIDATION قبل الإنشاء
            if vals.get("cr_operation_type_id"):
                ptype = self.env["stock.picking.type"].browse(vals["cr_operation_type_id"])
                if ptype.is_component_receiving_enabled and not vals.get("origin"):
                    raise ValidationError("Source Document is required in Component Receiving!")

        # تابع الإنشاء
        records = super().create(vals_list)

        # VALIDATIONS بعد الإنشاء
        for rec in records:
            rec._validate_owner_partner_match()
            rec._validate_origin_required()

        return records

    # ============================================================
    # 7) WRITE override
    # ============================================================
    def write(self, vals):
        result = super().write(vals)

        self._validate_owner_partner_match()
        self._validate_origin_required()

        return result
