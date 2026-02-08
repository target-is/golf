# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _


class IrModel(models.Model):
    # This class extends the 'ir.model' model to introduce an 'abstract' field
    # and modifies the 'display_name' based on the 'is_access_rights' context.
    # This allows dynamic modification of the model's display name for access-rights-sensitive contexts.

    _inherit = 'ir.model'

    abstract = fields.Boolean('Abstract', readonly=True)

    @api.depends('name')
    @api.depends_context('is_access_rights')
    def _compute_display_name(self):
        """
        Computes the display name for the ir.model records.
        If 'is_access_rights' context is set, modify the display name format to include both model name and model's model field.
        """
        if not self.env.context.get('is_access_rights'):
            return super()._compute_display_name()  # Calls the base method from 'ir.model'
        for model in self:
            new_name = "{} ({})".format(model.name, model.model)
            model.display_name = new_name


class IrModelField(models.Model):
    # This class extends the 'ir.model.fields' model to modify the 'display_name' of fields.
    # If the 'is_access_rights' context is active, the display name includes both the field description
    # and the model to which the field belongs, providing more contextual information.
    _inherit = 'ir.model.fields'

    @api.depends('model_id')
    @api.depends_context('is_access_rights')
    def _compute_display_name(self):
        """
        Computes the display name for the ir.model.fields records.
        If 'is_access_rights' context is set, modify the display name format to include field description and model.
        """
        if not self.env.context.get('is_access_rights'):
            return super()._compute_display_name()  # Calls the base method from 'ir.model.fields'
        for field in self:
            new_name = "{} => {} ({})".format(field.field_description, field.name, field.model_id.model)
            field.display_name = new_name


class IrUiView(models.Model):
    # This class extends the 'ir.ui.view' model to modify the 'display_name' of views based on the 'is_access_rights' context.
    # It appends the model name to the view name, providing more detailed information about the view context when the access rights context is active.
    _inherit = 'ir.ui.view'

    @api.depends('model_id')
    @api.depends_context('is_access_rights')
    def _compute_display_name(self):
        """
        Computes the display name for the ir.ui.view records.
        If 'is_access_rights' context is set, modify the display name format to include view name and model.
        """
        if not self.env.context.get('is_access_rights'):
            return super()._compute_display_name()  # Calls the base method from 'ir.ui.view'
        for view in self:
            new_name = "{} ({})".format(view.name, view.model)
            view.display_name = new_name


class IrModuleModule(models.Model):
    # This class extends the 'ir.module.module' model to override the button functions for installing or upgrading modules.
    # It ensures that when modules are installed or upgraded, the 'abstract' field for models, such as 'Email Thread',
    # is updated according to the model's abstract setting.
    _inherit = 'ir.module.module'

    def _button_immediate_function(self, function):
        """
        Overrides the immediate function for button actions (install/upgrade).
        When a button related to installation or upgrade is triggered, checks the models for 'Email Thread' and updates abstract attribute.
        """
        res = super(IrModuleModule, self)._button_immediate_function(function)
        if function.__name__ in ['button_install', 'button_upgrade']:
            for record in self.env['ir.model'].search([]):
                if record.name == 'Email Thread':
                    pass  # Skips updating the 'abstract' attribute for 'Email Thread' model
                record.abstract = self.env[record.model]._abstract  # Updates the abstract field based on the model
        return res
