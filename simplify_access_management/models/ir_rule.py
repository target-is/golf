# -*- coding: utf-8 -*-
# Updated for Odoo 18 compatibility
# This file overrides the `ir.rule` model to introduce custom access control mechanisms,
# ensuring that domain rules apply based on the "simplify_access_management" module's status and user access settings.

from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError, UserError
from odoo.tools import config
from odoo.osv import expression
from odoo.tools.safe_eval import safe_eval
from odoo.http import request
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.addons.advanced_web_domain_widget.models.domain_prepare import prepare_domain_v2


class IrRule(models.Model):
    _inherit = 'ir.rule'

    @api.model
    @tools.conditional('xml' not in config['dev_mode'],
                       tools.ormcache('self.env.uid', 'self.env.su', 'model_name', 'mode',
                                      'tuple(self._compute_domain_context_values())'),
                       )
    def _compute_domain(self, model_name, mode="read"):
        """
        Override Odoo's default `_compute_domain` to apply custom access restrictions based on user permissions
        and the "simplify_access_management" module status.
        """
        # Call the base implementation first
        res = super(IrRule, self)._compute_domain(model_name, mode)

        # Check if the simplify_access_management module is installed
        read_value = True
        self._cr.execute("SELECT state FROM ir_module_module WHERE name='simplify_access_management'")
        module_state = self._cr.fetchone() or False

        # Check for modules pending upgrade, removal, or installation
        self._cr.execute("SELECT id FROM ir_module_module WHERE state IN ('to upgrade', 'to remove', 'to install')")
        pending_module_changes = self._cr.fetchone() or False

        if module_state and module_state[0] != 'installed':
            read_value = False

        excluded_models = ['mail.activity', 'res.users.log', 'res.users', 'mail.channel', 'mail.alias', 'bus.presence',
                           'res.lang']

        if self.env.user.id and read_value and not pending_module_changes:
            if model_name not in excluded_models:
                # Check for read-only user configuration
                self._cr.execute("""
                    SELECT am.id FROM access_management as am
                    WHERE active='t' AND readonly = True AND am.id 
                    IN (SELECT au.access_management_id 
                        FROM access_management_users_rel_ah as au 
                        WHERE user_id = %s AND am.id 
                        IN (SELECT ac.access_management_id
                            FROM access_management_comapnay_rel as ac))
                """ % self.env.user.id)
                readonly_users = self._cr.fetchall()

                if bool(readonly_users):
                    if mode != 'read' and model_name not in ['mail.channel.partner']:
                        raise UserError(_('%s is a read-only user. Changes are not allowed!') % self.env.user.name)

        # Check if `uninstall_simplify_access_management` parameter is set
        self._cr.execute("SELECT value FROM ir_config_parameter WHERE key='uninstall_simplify_access_management'")
        uninstall_value = self._cr.fetchone()

        if not uninstall_value:
            # Verify the simplify_access_management module's installation state
            self._cr.execute("SELECT state FROM ir_module_module WHERE name = 'simplify_access_management'")
            module_install_state = self._cr.fetchone()
            module_installed = module_install_state and module_install_state[0] == 'installed'

            if model_name and module_installed:
                # Retrieve the numeric ID of the model
                self._cr.execute("SELECT id FROM ir_model WHERE model=%s", [model_name])
                model_numeric_id = self._cr.fetchone()
                model_numeric_id = model_numeric_id and model_numeric_id[0] or False

                if model_numeric_id and isinstance(model_numeric_id, int):
                    try:
                        self._cr.execute("""
                            SELECT dm.id
                            FROM access_domain_ah as dm
                            WHERE dm.model_id=%s AND dm.apply_domain AND dm.access_management_id 
                            IN (SELECT am.id 
                                FROM access_management as am 
                                WHERE active='t' AND am.id 
                                IN (SELECT amusr.access_management_id
                                    FROM access_management_users_rel_ah as amusr
                                    WHERE amusr.user_id=%s))
                        """, [model_numeric_id, self.env.user.id])

                        access_domain_ah_ids = self.env['access.domain.ah'].browse(
                            row[0] for row in self._cr.fetchall()
                        ).filtered(
                            lambda line: self.env.company in line.access_management_id.company_ids
                        )
                    except Exception:
                        access_domain_ah_ids = False

                    if access_domain_ah_ids:
                        domain_list = []
                        company_domain = []
                        all_company = self.env['res.company'].sudo().search([]).ids

                        if model_name == 'res.partner':
                            self._cr.execute("SELECT partner_id FROM res_users")
                            partner_ids = [row[0] for row in self._cr.fetchall()]
                            domain_list = ['|', ('id', 'in', partner_ids)]

                        eval_context = self._eval_context()

                        for access in access_domain_ah_ids.sudo():
                            dom = safe_eval(access.domain, eval_context) if access.domain else []

                            if dom:
                                dom = expression.normalize_domain(dom)
                                for dom_tuple in dom:
                                    if isinstance(dom_tuple, tuple):
                                        left_user, left_company = False, False
                                        left_value_split_list = dom_tuple[0].split('.')
                                        model_string = model_name

                                        for field in left_value_split_list:
                                            model_obj = self.env[model_string]
                                            field_def = model_obj.sudo()._fields.get(field)

                                            if not field_def:
                                                break
                                            field_type = field_def.type

                                            if field_type in ['many2one', 'many2many', 'one2many']:
                                                field_relation = model_obj.fields_get()[field]['relation']
                                                model_string = field_relation

                                                if model_string == 'res.users':
                                                    left_user = True
                                                if model_string == 'res.company':
                                                    left_company = True

                                        if left_user and 0 in dom_tuple[2]:
                                            dom_tuple[2][dom_tuple[2].index(0)] = self.env.user.id

                                        if left_company and 0 in dom_tuple[2]:
                                            dom_tuple[2][dom_tuple[2].index(0)] = self.env.company.id

                                    domain_list.append(dom_tuple)

                                if company_domain:
                                    return company_domain
                                return domain_list

        return res