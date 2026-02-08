# -*- coding: utf-8 -*-
# This module extends the 'res.users' model to integrate access management functionalities.
# It enforces read-only restrictions for certain users based on the defined access management settings.
# Additionally, it overrides the login process to handle scenarios where login is disabled.
# Odoo Version: 18

from odoo import fields, models, api, SUPERUSER_ID, _
from odoo.exceptions import UserError, AccessDenied
import logging

_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = 'res.users'

    # Many-to-many relationship with access.management model
    access_management_ids = fields.Many2many('access.management',
                                             'access_management_users_rel_ah',
                                             'user_id',
                                             'access_management_id',
                                             'Access Pack')

    def write(self, vals):
        """
        Overrides the write method to enforce read-only restrictions on admin users
        based on access management settings.
        """
        res = super(ResUsers, self).write(vals)

        for user in self:
            for access in user.access_management_ids:
                if user.env.company in access.company_ids and access.readonly:
                    if user.has_group('base.group_system') or user.has_group('base.group_erp_manager'):
                        raise UserError(_('Admin user cannot be set as read-only!'))

        return res

    @api.model_create_multi
    def create(self, vals_list):
        """
        Overrides the create method to enforce read-only restrictions on admin users
        based on access management settings.
        """
        res = super(ResUsers, self).create(vals_list)

        for record in res:
            for access in record.access_management_ids:
                # Ensure the user cannot be set to read-only if they are an admin user
                if self.env.company in access.company_ids and access.readonly:
                    if record.has_group('base.group_system') or record.has_group('base.group_erp_manager'):
                        raise UserError(_('Admin user cannot be set as read-only!'))
        return res

    @classmethod
    def _login(cls, db, credential, user_agent_env):
        """
        Overrides the login process to check whether login is disabled for certain users.
        If login is disabled, raises an AccessDenied exception.
        """
        # TODO : test this  later
        try:
            # Call the original login method
            res = super(ResUsers, cls)._login(db, credential, user_agent_env=user_agent_env)

            # Check if login is disabled for the current user based on the access management settings
            with cls.pool.cursor() as cr:
                self = api.Environment(cr, SUPERUSER_ID, {})[cls._name]
                access_management_obj = self.env['access.management']

                # Raise AccessDenied if login is disabled for the user
                if access_management_obj.search([('user_ids', 'in', [res.get('uid')]),('disable_login', '=', True)]):
                    raise AccessDenied()

        except AccessDenied:
            _logger.info("Login failed for db:%s, login:%s", db, credential['login'])
            raise

        return res



