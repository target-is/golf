# -*- coding: utf-8 -*-
# This model is an upgraded version of the Remove Action model for Odoo 18.
# It manages access restrictions for models, including hiding views, actions, and buttons for specific users.
# Changes include compatibility updates for Odoo 18 and detailed comments for maintainability.

from odoo import fields, models, api, _


class RemoveAction(models.Model):
    _name = 'remove.action'
    _description = "Models Right"

    # Reference to the parent access management record
    access_management_id = fields.Many2one(
        'access.management',
        string='Access Management',
        help="The access management configuration related to this record."
    )

    # The model where restrictions will apply
    model_id = fields.Many2one(
        'ir.model',
        string='Model',
        help="The model to which the access restrictions apply."
    )

    # Views to hide in the selected model
    view_data_ids = fields.Many2many(
        'view.data',
        'remove_action_view_data_rel_ah',
        'remove_action_id',
        'view_data_id',
        string='Hide Views',
        help="The views listed here will be hidden in the selected model for the defined users."
    )

    # Server actions to hide in the selected model
    server_action_ids = fields.Many2many(
        'action.data',
        'remove_action_server_action_data_rel_ah',
        'remove_action_id',
        'server_action_id',
        string='Hide Actions',
        domain="[('action_id.binding_model_id','=',model_id),('action_id.type','!=','ir.actions.report')]",
        help="The server actions listed here will be hidden in the selected model for the defined users."
    )

    # Reports to hide in the selected model
    report_action_ids = fields.Many2many(
        'action.data',
        'remove_action_report_action_data_rel_ah',
        'remove_action_id',
        'report_action_id',
        string='Hide Reports',
        domain="[('action_id.binding_model_id','=',model_id),('action_id.type','=','ir.actions.report')]",
        help="The reports listed here will be hidden in the selected model for the defined users."
    )

    # Restriction settings
    restrict_export = fields.Boolean(
        string='Hide Export',
        help="The Export button will be hidden in the selected model for the defined users."
    )
    restrict_import = fields.Boolean(
        string='Hide Import',
        help="The Import button will be hidden in the selected model for the defined users."
    )
    readonly = fields.Boolean(
        string='Read-Only',
        help="The selected model will be made read-only for the defined users."
    )

    # Button-specific restrictions
    restrict_create = fields.Boolean(
        string='Hide Create',
        help="The Create button will be hidden in the selected model for the defined users."
    )
    restrict_edit = fields.Boolean(
        string='Hide Edit',
        help="The Edit button will be hidden in the selected model for the defined users."
    )
    restrict_delete = fields.Boolean(
        string='Hide Delete',
        help="The Delete button will be hidden in the selected model for the defined users."
    )
    restrict_archive_unarchive = fields.Boolean(
        string='Hide Archive/Unarchive',
        help="The Archive and Unarchive actions will be hidden in the selected model for the defined users."
    )
    restrict_duplicate = fields.Boolean(
        string='Hide Duplicate',
        help="The Duplicate action will be hidden in the selected model for the defined users."
    )

    # Other restrictions
    restrict_chatter = fields.Boolean(
        string='Hide Chatter',
        help="The Chatter feature will be hidden in the selected model for the defined users."
    )
    restrict_spreadsheet = fields.Boolean(
        string='Hide Spreadsheet',
        help="The Spreadsheet feature will be hidden in the selected model for the defined users."
    )
