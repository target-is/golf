from odoo import models, fields, api

from odoo.exceptions import ValidationError


class RepairOrder(models.Model):
    _inherit = "repair.order"

    approval_line_ids = fields.One2many(
        "repair.approval.line",
        "repair_id",
        string="Approval Lines"
    )


class StockMove(models.Model):
    _inherit = "stock.move"

    @api.model
    def create(self, vals_list):
        # detect if created from UI (NOT backend)
        is_ui_create = not self.env.context.get("from_backend", False)

        for vals in vals_list:
            # check if it is related to Repair
            repair_id = vals.get("repair_id")
            if repair_id and is_ui_create:
                # user is not sales → forbid creation
                if not self.env.user.has_group("sales_team.group_sale_salesman") and \
                   not self.env.user.has_group("sales_team.group_sale_salesman_all_leads") and \
                   not self.env.user.has_group("sales_team.group_sale_manager"):
                    raise ValidationError("❌ Only Sales users can add Parts manually.")

        return super().create(vals_list)
