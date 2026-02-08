# -*- coding: utf-8 -*-
# This model is an upgraded version of the Action Data model for Odoo 18.
# It stores metadata related to actions in the Odoo system.
# Changes from the Odoo 17 version include adjustments for compatibility with Odoo 18 standards
# and improved clarity through comments.

from odoo import fields, models, api, _


class ActionData(models.Model):
    _name = 'action.data'
    _description = "Action Data"

    # The name of the action data entry
    name = fields.Char(
        string='Name',
        required=True,
        help="The name of the action data entry."
    )

    # Reference to the related action
    action_id = fields.Many2one(
        'ir.actions.actions',
        string='Action',
        ondelete='cascade',
        required=True,
        help="The action this data entry is associated with."
    )
