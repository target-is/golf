# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
# This module extends the base model to manage access control and permissions in Odoo.
# It handles the dynamic customization of views, toolbars, and actions based on user access rights.
# Key Features:
# 1. Customizes the visibility of actions and print buttons in the form and tree views based on user permissions.
# 2. Ensures user access to records is limited based on domain and rights specified in access management.
# 3. Controls the visibility of specific UI components such as the chatter and import/export buttons.
# 4. Provides granular control over create, edit, delete, and read operations through access management rules.
# 5. Prevents users from performing certain operations (create, write, unlink) if they lack the necessary rights.
# 6. Integrates with the advanced web domain widget for dynamic domain management.
#
# Author: [Your Name]
# License: [Your License Info]


from odoo import api, fields, models, tools, _
from odoo.osv import expression
from odoo.exceptions import UserError

class BaseModel(models.AbstractModel):
    _inherit = 'base'

    @api.model
    def get_views(self, views, options=None):
        """
        Overridden method to control the views, especially the toolbar actions
        in form and tree views based on user access management.
        """
        res = super().get_views(views, options)

        # Get the toolbar sections for form and tree views
        form_toolbar = res['views'].get('form', {}).get('toolbar') or False
        tree_toolbar = res['views'].get('list', {}).get('toolbar') or False

        # Search for remove actions based on the access management for the current company and user
        remove_action = self.env['remove.action'].search(
            [('access_management_id.company_ids', 'in', self.env.company.id),
             ('access_management_id', 'in', self.env.user.access_management_ids.ids),
             ('model_id.model', '=', self._name)]
        )

        if form_toolbar or tree_toolbar:
            remove_server_action = remove_action.mapped('server_action_ids.action_id').ids
            remove_print_action = remove_action.mapped('report_action_ids.action_id').ids

        # Remove server actions and print actions from the toolbar based on the access rules
        if form_toolbar:
            if 'action' in res['views']['form']['toolbar']:
                res['views']['form']['toolbar']['action'] = [
                    rec for rec in res['views']['form']['toolbar']['action']
                    if rec.get('id', False) not in remove_server_action
                ]
            if 'print' in res['views']['form']['toolbar']:
                res['views']['form']['toolbar']['print'] = [
                    rec for rec in res['views']['form']['toolbar']['print']
                    if rec.get('id', False) not in remove_print_action
                ]

        if tree_toolbar:
            if 'action' in res['views']['list']['toolbar']:
                res['views']['list']['toolbar']['action'] = [
                    rec for rec in res['views']['list']['toolbar']['action']
                    if rec.get('id', False) not in remove_server_action
                ]
            if 'print' in res['views']['list']['toolbar']:
                res['views']['list']['toolbar']['print'] = [
                    rec for rec in res['views']['list']['toolbar']['print']
                    if rec.get('id', False) not in remove_print_action
                ]
        return res

    @api.model
    def load_views(self, views, options=None):
        """
        Override the method to load views while checking for restricted actions
        and removing views according to the user's access rules.
        """
        actions_and_prints = []
        remove_actions = self.env['remove.action'].search(
            [('access_management_id.company_ids', 'in', self.env.company.id),
             ('access_management_id', 'in', self.env.user.access_management_ids.ids),
             ('model_id.model', '=', self._name)]
        )

        # Collect actions and print actions to remove based on access rules
        for access in remove_actions:
            actions_and_prints.extend(access.mapped('report_action_ids.action_id').ids)
            actions_and_prints.extend(access.mapped('server_action_ids.action_id').ids)

            # Remove views that are restricted by the access management
            for view_data in access.view_data_ids:
                for view_data_list in views:
                    if view_data.techname == view_data_list[1]:
                        views.remove(view_data_list)

        res = super(BaseModel, self).load_views(views, options=options)

        # Remove toolbar actions (action/print) based on access control
        if 'fields_views' in res:
            for view in ['list', 'form']:
                if view in res['fields_views']:
                    if 'toolbar' in res['fields_views'][view]:
                        if 'print' in res['fields_views'][view]['toolbar']:
                            res['fields_views'][view]['toolbar']['print'] = [
                                pri for pri in res['fields_views'][view]['toolbar']['print']
                                if pri['id'] not in actions_and_prints
                            ]
                        if 'action' in res['fields_views'][view]['toolbar']:
                            res['fields_views'][view]['toolbar']['action'] = [
                                act for act in res['fields_views'][view]['toolbar']['action']
                                if act['id'] not in actions_and_prints
                            ]

        return res

    @api.model
    def _get_view(self, view_id=None, view_type='form', **options):
        arch, view = super()._get_view(view_id, view_type, **options)
        access_management_obj = self.env['access.management']
        # cids = request.httprequest.cookies.get('cids') and request.httprequest.cookies.get('cids').split(',')[0] or request.env.company.id
        readonly_access_id = access_management_obj.search(
            [('company_ids', 'in', self.env.company.id), ('active', '=', True), ('user_ids', 'in', self.env.user.id),
             ('readonly', '=', True)])

        access_recs = self.env['access.domain.ah'].search(
            [('access_management_id.company_ids', 'in', self.env.company.id),
             ('access_management_id.user_ids', 'in', self.env.user.id), ('access_management_id.active', '=', True),
             ('model_id.model', '=', self._name)])

        access_model_recs = self.env['remove.action'].search(
            [('access_management_id.company_ids', 'in', self.env.company.id),
             ('access_management_id.user_ids', 'in', self.env.user.id),
             ('access_management_id.active', '=', True),
             ('model_id.model', '=', self._name)])
        if view_type == 'form':
            access_management_id = access_management_obj.search([('company_ids', 'in', self.env.company.id),
                                                                 ('active', '=', True),
                                                                 ('user_ids', 'in', self.env.user.id),
                                                                 ('hide_chatter', '=', True)],
                                                                limit=1).id
            if access_management_id:
                for chatter in arch.xpath("//chatter"):
                    chatter.getparent().remove(chatter)

            else:
                if self.env['hide.chatter'].search([('access_management_id.company_ids', 'in', self.env.company.id),
                                                    ('access_management_id.active', '=', True),
                                                    ('access_management_id.user_ids', 'in', self.env.user.id),
                                                    ('model_id.model', '=', self._name),
                                                    ('hide_chatter', '=', True)],
                                                   limit=1):

                    for chatter in arch.xpath("//chatter"):
                        chatter.getparent().remove(chatter)

        if view_type in ['kanban', 'list']:
            restrict_import = access_management_obj.search([('company_ids', 'in', self.env.company.id),
                                                            ('active', '=', True),
                                                            ('user_ids', 'in', self.env.user.id),
                                                            ('hide_import', '=', True)], limit=1).id

            if access_model_recs.filtered(lambda x: x.restrict_import) or restrict_import:
                doc = arch
                doc.attrib.update({'import': 'false'})
                arch = doc

            restrict_export = access_management_obj.search([('company_ids', 'in', self.env.company.id),
                                                            ('active', '=', True),
                                                            ('user_ids', 'in', self.env.user.id),
                                                            ('hide_export', '=', True)], limit=1).id

            if access_model_recs.filtered(lambda x: x.restrict_export) or restrict_export:
                doc = arch
                doc.attrib.update({'export_xlsx': 'false'})
                arch = doc

        if readonly_access_id:
            if view_type == 'form':
                arch.attrib.update({'create': 'false', 'delete': 'false', 'edit': 'false'})

            if view_type == 'list':
                arch.attrib.update({'create': 'false', 'delete': 'false', 'edit': 'false'})

            if view_type == 'kanban':
                arch.attrib.update({'create': 'false', 'delete': 'false', 'edit': 'false'})

        else:

            if access_model_recs:
                delete = 'true'
                edit = 'true'
                create = 'true'
                for access_model in access_model_recs:
                    if access_model.restrict_create:
                        create = 'false'
                    if access_model.restrict_edit:
                        edit = 'false'
                    if access_model.restrict_delete:
                        delete = 'false'

                if view_type == 'form':
                    arch.attrib.update({'create': create, 'delete': delete, 'edit': edit})

                if view_type == 'list':
                    arch.attrib.update({'create': create, 'delete': delete, 'edit': edit})

                if view_type == 'kanban':
                    arch.attrib.update({'create': create, 'delete': delete, 'edit': edit})

            if access_recs:
                delete = 'false'
                edit = 'false'
                create = 'false'
                for access_rec in access_recs:
                    if access_rec.create_right:
                        create = 'true'
                    if access_rec.write_right:
                        edit = 'true'
                    if access_rec.delete_right:
                        delete = 'true'

                if view_type == 'form':
                    arch.attrib.update({'create': create, 'delete': delete, 'edit': edit})

                if view_type == 'list':
                    arch.attrib.update({'create': create, 'delete': delete, 'edit': edit})

                if view_type == 'kanban':
                    arch.attrib.update({'create': create, 'delete': delete, 'edit': edit})

        return arch, view

    def _get_access_management_domain_record(self, model=False):
        """
        Retrieves access domain records based on the model and the user's access management.
        """
        records = None
        try:
            if model:
                model_numeric_id = self.env['ir.model'].search([('model', '=', model)], limit=1).id
                if model_numeric_id:
                    records = self.env['access.domain.ah'].search([
                        ('model_id', '=', model_numeric_id),
                        ('access_management_id.user_ids', 'in', self.env.user.id)
                    ])
        except Exception:
            pass
        return records

    def _check_access_management_right(self, mode='write', records=None):
        """
        Checks whether the current user has the right to perform a specific operation
        (create, write, or delete) on the given records.
        """
        access_flag = False
        access_rule = None
        for record in records:
            if mode == 'create' and record.create_right:
                access_flag = True
            elif mode == 'write' and record.write_right:
                access_flag = True
            elif mode == 'unlink' and record.delete_right:
                access_flag = True

        return {'access_flag': access_flag, 'access_rule': access_rule}

    def unlink(self):
        # Skip during module uninstall or technical model deletions
        if self.env.context.get('module_uninstall') or self._name == 'ir.model.data':
            return super(BaseModel, self).unlink()

        for rec in self:
            access_domain_ah_ids = rec._get_access_management_domain_record(model=rec._name)
            if access_domain_ah_ids:
                flag = rec._check_access_management_right(mode='unlink', records=access_domain_ah_ids)
                if not flag['access_flag']:
                    raise UserError(_("Access Denied: You cannot delete this record due to access management rules."))

        return super(BaseModel, self).unlink()

    def write(self, vals):
        """
        Overridden write method to ensure access control before updating records.
        """
        for rec in self:
            access_domain_ah_ids = rec._get_access_management_domain_record(model=rec._name)
            if access_domain_ah_ids:
                flag = rec._check_access_management_right(mode='write', records=access_domain_ah_ids)
                if not flag['access_flag']:
                    rec._display_access_management_error(mode='write', rule=flag['access_rule'])

        return super(BaseModel, self).write(vals)

    @api.model
    def _name_search(self, name, domain=None, operator='ilike', limit=None, order=None):
        if not self.env.context.get('is_access_rights'):
            return super(BaseModel,self)._name_search(name, domain, operator, limit, order)
        domain = expression.AND([domain,[('name', 'ilike', name)]])
        return self._search(domain, limit=limit, order=order)