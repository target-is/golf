from odoo import models, fields, api
from odoo.exceptions import ValidationError

class StockMove(models.Model):
    _inherit = 'stock.move'

    service_category = fields.Selection(
        related='product_id.service_types',
        string="Service Category",
        readonly=True,
        store=False,
    )
