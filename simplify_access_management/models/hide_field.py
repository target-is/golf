# -*- coding: utf-8 -*-
# This model manages the visibility, read-only, and required status of fields
# based on user-defined access management rules. It provides a way to hide,
# make read-only, or set certain fields as required for defined users within
# specific models.
# Odoo Version: 18

from odoo import fields, models, api, _
from lxml import etree


class HideField(models.Model):
    _name = 'hide.field'
    _description = "Fields Rights"

    access_management_id = fields.Many2one('access.management', 'Access Management')
    model_id = fields.Many2one('ir.model', 'Model')
    field_id = fields.Many2many('ir.model.fields', 'hide_field_ir_model_fields_rel', 'hide_field_id', 'ir_field_id',
                                'Field')
    invisible = fields.Boolean('Invisible',
                               help="Selected Field will be hidden in selected model from the defined users.")
    readonly = fields.Boolean('Read-Only',
                              help="Selected Field will be Read-only in selected model from the defined users.")
    required = fields.Boolean('Required',
                              help="Selected Field will be set as required for selected model from the defined users.")
    external_link = fields.Boolean('Remove External Link',
                                   help="External Link will be hidden for relational fields in selected model from the defined users.")