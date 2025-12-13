from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = "product.template"
    service_types = fields.Selection([
        ('battery', 'Battery Shop Services'),
        ('wheels', 'Wheels Shop Services'),
        ('ndt', 'NDT Testing Shop Services'),
        ('spare', 'Spare Parts Services'),
    ], string="Service Category")

    spareparts_line_ids = fields.One2many(
        'product.spareparts.line',
        'product_tmpl_id',
        string="Spare Parts Items"
    )

    is_spareparts = fields.Boolean(string="Is Spare Parts")

    @api.model_create_multi
    def create(self, vals_list):
        products = super().create(vals_list)
        for product, vals in zip(products, vals_list):
            if vals.get('is_spareparts'):
                product._notify_spare_parts_added()
        return products

    def write(self, vals):
        # نعرف الحالة القديمة قبل الكتابة
        old_values = {p.id: p.is_spareparts for p in self}

        res = super().write(vals)

        # بعد الكتابة
        if 'is_spareparts' in vals:
            for product in self:
                old = old_values[product.id]
                new = product.is_spareparts

                if not old and new:
                    # اتفعّل ✔
                    product._notify_spare_parts_added()

                elif old and not new:
                    # اتلغى ❌
                    product._notify_spare_parts_removed()

        return res

    # Notification when enabled
    def _notify_spare_parts_added(self):
        message = f"Product '{self.name}' is now Spare Parts"
        self.env['bus.bus']._sendone(
            self.env.user.partner_id,
            'simple_notification',
            {

                'message': message,
                'type': 'success',  # أخضر
                'sticky': False
            }
        )

    # Notification when disabled
    def _notify_spare_parts_removed(self):
        message = f"Product '{self.name}' is no longer Spare Parts"
        self.env['bus.bus']._sendone(
            self.env.user.partner_id,
            'simple_notification',
            {

                'message': message,
                'type': 'warning',  # أصفر
                'sticky': False
            }
        )
