# -*- coding: utf-8 -*-
# IrUiView Model Extension for Odoo
#
# This model extends the 'ir.ui.view' model to customize the behavior of user interface elements (fields, buttons, pages, etc.)
# based on the access rights of the current user. It provides functionality to:
# - Hide or disable fields, labels, buttons, notebook pages, and filters dynamically based on user permissions and settings.
# - Apply custom behavior to various view elements like fields, buttons, links, and more.
# - Ensure the UI reflects user-specific configurations regarding visibility, editability, and access control.
#
# The model leverages the 'hide.field' and 'hide.view.nodes' models to manage access control and visibility rules for different
# elements in the user interface, making sure that only relevant data and actions are shown to the user.
#
# This is a core customization to enhance user experience based on role-based access control (RBAC) in Odoo.

from odoo import models, SUPERUSER_ID, _
from odoo.http import request
import ast


class IrUiView(models.Model):
    _inherit = 'ir.ui.view'

    def _postprocess_tag_field(self, node, name_manager, node_info):
        super()._postprocess_tag_field(node, name_manager, node_info)
        try:
            hide_field_obj = self.env['hide.field'].sudo()
            if node.tag in ['field', 'label']:
                hide_field_records = hide_field_obj.search([
                    ('access_management_id.company_ids', 'in', self.env.company.id),
                    ('model_id.model', '=', name_manager.model._name),
                    ('access_management_id.active', '=', True),
                    ('access_management_id.user_ids', 'in', request.env.uid)
                ])

                for hide_field in hide_field_records:
                    for field_id in hide_field.field_id:
                        if (node.tag == 'field' and node.get('name') == field_id.name) or \
                                (node.tag == 'label' and node.get('for') == field_id.name):
                            if hide_field.external_link:
                                self._set_external_link_options(node)

                            if hide_field.invisible:
                                node_info['column_invisible'] = True
                                node.set('column_invisible', 'True')
                                node_info['invisible'] = True
                                node.set('invisible', '1')

                            if hide_field.readonly:
                                node_info['readonly'] = True
                                node.set('readonly', '1')
                                node.set('force_save', '1')

                            if hide_field.required:
                                node_info['required'] = True
                                node.set('required', '1')

        except Exception:
            pass

    def _set_external_link_options(self, node):
        """ Set external link options for the field """
        options_dict = {}
        if 'widget' in node.attrib:
            if node.attrib['widget'] in ['product_configurator', 'many2one_avatar_user']:
                del node.attrib['widget']

        if 'options' in node.attrib:
            options_dict = ast.literal_eval(node.attrib['options'])
            options_dict.update({"no_edit": True, "no_create": True, "no_open": True})
            node.attrib['options'] = str(options_dict)
        else:
            node.attrib.update({'can_create': 'false', 'can_write': 'false', 'no_open': 'true'})

    def _postprocess_tag_button(self, node, name_manager, node_info):
        # Hide Any Button
        postprocessor = getattr(super(IrUiView, self), '_postprocess_tag_button', False)
        if postprocessor:
            super(IrUiView, self)._postprocess_tag_button(node, name_manager, node_info)

        hide_button_obj = self.env['hide.view.nodes']
        hide_button_records = hide_button_obj.sudo().search([
            ('access_management_id.company_ids', 'in', self.env.company.id),
            ('model_id.model', '=', name_manager.model._name),
            ('access_management_id.active', '=', True),
            ('access_management_id.user_ids', 'in', request.env.uid)
        ])

        btn_store_model_nodes_ids = hide_button_records.mapped('btn_store_model_nodes_ids')
        if btn_store_model_nodes_ids:
            for btn in btn_store_model_nodes_ids:
                if btn.attribute_name == node.get('name'):
                    node.set('invisible', '1')
                    if 'attrs' in node.attrib:
                        del node.attrib['attrs']
                    node_info['invisible'] = True

        return None

    def _postprocess_tag_page(self, node, name_manager, node_info):
        # Hide Any Notebook Page
        postprocessor = getattr(super(IrUiView, self), '_postprocess_tag_page', False)
        if postprocessor:
            super(IrUiView, self)._postprocess_tag_page(node, name_manager, node_info)

        hide_tab_obj = self.env['hide.view.nodes']
        hide_tab_records = hide_tab_obj.sudo().search([
            ('access_management_id.company_ids', 'in', self.env.company.id),
            ('model_id.model', '=', name_manager.model._name),
            ('access_management_id.active', '=', True),
            ('access_management_id.user_ids', 'in', request.env.uid)
        ])

        page_store_model_nodes_ids = hide_tab_records.mapped('page_store_model_nodes_ids')
        if page_store_model_nodes_ids:
            for tab in page_store_model_nodes_ids:
                if self._is_tab_visible(tab, node):
                    node.set('invisible', '1')
                    if 'attrs' in node.attrib:
                        del node.attrib['attrs']
                    node_info['invisible'] = True

        return None

    def _is_tab_visible(self, tab, node):
        """ Check if a tab is visible based on the node and language """
        attribute_string = tab.attribute_string
        if tab.lang_code != self.env.lang:
            field = self.env['ir.ui.view']._fields['arch_db']
            translation_dict = field.get_translation_dictionary(
                self.with_context(lang=tab.lang_code).arch_db,
                {self.env.lang: self.with_context(lang=self.env.lang)['arch_db']}
            )
            attribute_string = translation_dict[attribute_string][self.env.lang]
        return attribute_string == node.get('string')

    def _postprocess_tag_a(self, node, name_manager, node_info):
        # Hide Any Notebook Page Link
        postprocessor = getattr(super(IrUiView, self), '_postprocess_tag_a', False)
        if postprocessor:
            super(IrUiView, self)._postprocess_tag_a(node, name_manager, node_info)

        hide_tab_obj = self.env['hide.view.nodes']
        hide_tab_records = hide_tab_obj.sudo().search([
            ('access_management_id.company_ids', 'in', self.env.company.id),
            ('model_id.model', '=', name_manager.model._name),
            ('access_management_id.active', '=', True),
            ('access_management_id.user_ids', 'in', request.env.uid)
        ])

        link_store_model_nodes_ids = hide_tab_records.mapped('link_store_model_nodes_ids')
        if link_store_model_nodes_ids:
            for link in link_store_model_nodes_ids:
                if _(link.attribute_name) == node.get('name'):
                    node.set('invisible', '1')
                    if 'attrs' in node.attrib:
                        del node.attrib['attrs']
                    node_info['invisible'] = True

        return None

    def _postprocess_tag_div(self, node, name_manager, node_info):
        # Hide Specific Div
        postprocessor = getattr(super(IrUiView, self), '_postprocess_tag_div', False)
        if postprocessor:
            super(IrUiView, self)._postprocess_tag_div(node, name_manager, node_info)

        hide_button_obj = self.env['hide.view.nodes'].sudo()

        if name_manager.model._name == 'res.config.settings' and node.tag == 'app' and node.get('string'):
            hide_button_records = hide_button_obj.search([
                ('access_management_id.company_ids', 'in', self.env.company.id),
                ('model_id.model', '=', name_manager.model._name),
                ('access_management_id.active', '=', True),
                ('access_management_id.user_ids', 'in', request.env.uid)
            ])

            for setting_tab in hide_button_records.mapped('page_store_model_nodes_ids'):
                if setting_tab.lang_code != self.env.lang:
                    field = self.env['ir.ui.view']._fields['arch_db']
                    translation_dict = field.get_translation_dictionary(
                        self.with_context(lang=setting_tab.lang_code).arch_db,
                        {self.env.lang: self.with_context(lang=self.env.lang)['arch_db']}
                    )
                    attribute_string = translation_dict[setting_tab.attribute_string][self.env.lang]
                else:
                    attribute_string = setting_tab.attribute_string

                if node.get('data-key') == setting_tab.attribute_name:
                    node_info['invisible'] = True
                    node.set('invisible', '1')

        return None

    def _postprocess_tag_filter(self, node, name_manager, node_info):
        # Hide Any Filter or Group
        postprocessor = getattr(super(IrUiView, self), '_postprocess_tag_filter', False)
        if postprocessor:
            super(IrUiView, self)._postprocess_tag_filter(node, name_manager, node_info)

        if node.tag in ['filter', 'group']:
            hide_filter_group_obj = self.env['hide.filters.groups'].sudo().search([
                ('access_management_id.company_ids', 'in', self.env.company.id),
                ('model_id.model', '=', name_manager.model._name),
                ('access_management_id.active', '=', True),
                ('access_management_id.user_ids', 'in', request.env.uid)
            ])

            for hide_field_obj in hide_filter_group_obj:
                for hide_filter in hide_field_obj.filters_store_model_nodes_ids.mapped('attribute_name'):
                    if hide_filter == node.get('name'):
                        node_info['invisible'] = True
                        node.set('invisible', '1')

                for hide_field_obj in hide_filter_group_obj:
                    for hide_filter in hide_field_obj.groups_store_model_nodes_ids.mapped('attribute_name'):
                        if hide_filter == node.get('name'):
                            node_info['invisible'] = True
                            node.set('invisible', '1')

        return None

    def _postprocess_tag_label(self, node, name_manager, node_info):
        postprocessor = getattr(super(IrUiView, self), '_postprocess_tag_label', False)
        hide_field_obj = self.env['hide.field'].sudo()
        if postprocessor:
            super(IrUiView, self)._postprocess_tag_label(node, name_manager, node_info)
            if node.get('for'):
                for hide_field in hide_field_obj.search([
                        ('access_management_id.company_ids', 'in', self.env.company.id),
                        ('model_id.model', '=', name_manager.model._name),
                        ('access_management_id.active', '=', True),
                        ('access_management_id.user_ids', 'in', request.env.uid)]):
                    for field_id in hide_field.field_id:
                        if node.get('for') == field_id.name and node.get('string') == field_id.field_description:
                            node_info['invisible'] = True
                            node.set('invisible', '1')
