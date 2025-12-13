from odoo import models, fields


class ProductSparePartsLine(models.Model):
    _name = "product.spareparts.line"
    _description = "Spare Parts Lines"

    product_tmpl_id = fields.Many2one("product.template")

    spare_product_id = fields.Many2one(
        "product.product",
        string="Spare Part",
        domain="[('is_spareparts','=',True)]"
    )

    # ======== RELATED FIELDS FROM PRODUCT ===========
    cost = fields.Float(
        related="spare_product_id.product_tmpl_id.standard_price",
        string="Cost",
        readonly=True
    )

    sales_price = fields.Float(
        related="spare_product_id.product_tmpl_id.list_price",
        string="Sales Price",
        readonly=True
    )

    quantity_on_hand = fields.Float(
        related="spare_product_id.qty_available",
        string="Quantity On Hand",
        readonly=True
    )
