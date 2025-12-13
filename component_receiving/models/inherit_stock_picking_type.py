from odoo import models, fields, api
from odoo.exceptions import ValidationError


# -------------------------------------------------------------
# Extend Stock Picking Type – Add CR Checkbox and Restrict One
# -------------------------------------------------------------
class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'

    is_component_receiving_enabled = fields.Boolean(
        string="Enable for Component Receiving",
        help="Operation type allowed for Component Receiving."
    )

    @api.constrains('is_component_receiving_enabled')
    def _check_only_one_component_operation_enabled(self):
        for rec in self:
            if rec.is_component_receiving_enabled:
                exists = self.search([
                    ('id', '!=', rec.id),
                    ('is_component_receiving_enabled', '=', True)
                ], limit=1)
                if exists:
                    raise ValidationError(
                        f"Component Receiving can only have one activated operation type (Already: {exists.name})."
                    )



    select_service = fields.Selection([
        ('battery', 'Battery Shop Services'),
        ('wheels', 'Wheels Shop Services'),
        ('ndt', 'NDT Testing Shop Services'),
        ('spare', 'Spare Parts Services'),
    ], string="Service Category", required=False)

    @api.constrains('select_service')
    def _check_unique_service(self):
        for rec in self:
            if rec.select_service:
                exists = self.search([
                    ('id', '!=', rec.id),
                    ('select_service', '=', rec.select_service)
                ], limit=1)

                if exists:
                    raise ValidationError(
                        f"❌ Operation Type '{exists.name}' is already assigned to service '{dict(self._fields['select_service'].selection).get(rec.select_service)}'.\n"
                        f"You cannot assign the same service to more than one Operation Type."
                    )
