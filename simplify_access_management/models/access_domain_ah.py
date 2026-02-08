# -*- coding: utf-8 -*-
# This model is an upgraded version of the Access Domain model for Odoo 18.
# It defines rules for access rights and domains applied to models in the system.
# Changes from the Odoo 17 version include updates for compatibility with Odoo 18 standards
# and enhanced readability with comments for maintainability.

from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError

class AccessDomainAh(models.Model):
    _name = 'access.domain.ah'
    _description = 'Access Domain'

    # Reference to the model being accessed
    model_id = fields.Many2one(
        'ir.model',
        string='Model',
        index=True,
        required=True,
        ondelete='cascade'
    )
    # Related field to show the technical name of the model
    model_name = fields.Char(
        string='Model Name',
        related='model_id.model',
        readonly=True,
        store=True
    )

    # Boolean to determine if a custom domain filter is applied
    apply_domain = fields.Boolean(
        'Apply Filter',
        default=False
    )
    # Domain string to filter records for the model
    domain = fields.Char(
        string='Filter',
        default='[]',
        help="Create a custom domain rule to filter specific fields and records."
    )

    # Relationship to the access management parent model
    access_management_id = fields.Many2one(
        'access.management',
        string='Access Management'
    )

    # Access rights settings
    read_right = fields.Boolean(
        'Read',
        default=True,
        help="Grant 'Read' access to the selected model for specified users."
    )
    create_right = fields.Boolean(
        'Create',
        default=False,
        help="Grant 'Create' access to the selected model for specified users."
    )
    write_right = fields.Boolean(
        'Write',
        default=False,
        help="Grant 'Write' access to the selected model for specified users."
    )
    delete_right = fields.Boolean(
        'Delete',
        default=False,
        help="Grant 'Delete' access to the selected model for specified users."
    )

    # Triggered when 'apply_domain' changes to reset the domain if unchecked
    @api.onchange('apply_domain')
    def _onchange_apply_domain(self):
        for rec in self:
            if not rec.apply_domain:
                rec.domain = '[]'

    # Adjust related rights when 'read_right' changes
    @api.onchange('read_right')
    def _onchange_read_right(self):
        for rec in self:
            if not rec.read_right:
                rec.create_right = False
                rec.write_right = False
                rec.delete_right = False
                rec.apply_domain = True
                rec.domain = '[["id","=",False]]'  # Deny all records

    # Ensure 'read_right' is true if 'create_right' is granted
    @api.onchange('create_right')
    def _onchange_create_right(self):
        for rec in self:
            if rec.create_right:
                rec.read_right = True
            else:
                rec.delete_right = False

    # Ensure 'read_right' is true if 'write_right' is granted
    @api.onchange('write_right')
    def _onchange_write_right(self):
        for rec in self:
            if rec.write_right:
                rec.read_right = True
            else:
                rec.delete_right = False

    # Ensure 'read_right' and 'write_right' are true if 'delete_right' is granted
    @api.onchange('delete_right')
    def _onchange_delete_right(self):
        for rec in self:
            if rec.delete_right:
                rec.read_right = True
                rec.write_right = True
