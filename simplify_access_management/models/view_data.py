# -*- coding: utf-8 -*-
# This model is an upgraded version of the View Data model for Odoo 18.
# It stores metadata about views in the Odoo system, including technical names.
# Changes from the Odoo 17 version include compatibility updates for Odoo 18
# and detailed comments for improved understanding and maintainability.

from odoo import fields, models, api, _


class ViewData(models.Model):
    _name = 'view.data'
    _description = "View Data"

    # The name of the view data entry
    name = fields.Char(
        string='Name',
        required=True,
        help="The display name of the view data entry."
    )

    # The technical name of the view
    techname = fields.Char(
        string='Technical Name',
        required=True,
        help="The internal technical name of the view."
    )
