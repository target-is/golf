# -*- coding: utf-8 -*-
# IrModuleModule Extension for Odoo 18
#
# This model extends the 'ir.module.module' model to customize the uninstallation process of modules in Odoo 18.
# Specifically, it overrides the 'button_immediate_uninstall' method to manage the 'simplify_access_management' module.
#
# The key functionalities provided by this extension include:
# - Ensuring that a configuration parameter ('uninstall_simplify_access_management') is set to 'True' when the module is being uninstalled.
# - Creating the configuration parameter if it does not already exist, and removing it after the uninstallation is complete.
#
# This extension customizes the uninstallation behavior of the 'simplify_access_management' module to ensure proper tracking and cleanup
# of related configuration parameters.

from odoo import models, fields, api, _


class IrModuleModule(models.Model):
    _inherit = "ir.module.module"

    def button_immediate_uninstall(self):
        # Accessing the configuration parameter model to manage uninstall parameters
        config_parameter_obj = self.env['ir.config_parameter'].sudo()

        if self.name == 'simplify_access_management':
            # Search for existing configuration parameter or create a new one
            value = config_parameter_obj.search([('key', '=', 'uninstall_simplify_access_management')], limit=1)
            if value:
                value.value = 'True'
            else:
                config_parameter_obj.create({'key': 'uninstall_simplify_access_management', 'value': 'True'})

        # Call the original uninstallation method from the inherited model
        res = super(IrModuleModule, self).button_immediate_uninstall()

        # Clean up the configuration parameter after uninstallation
        config_parameter_obj.search([('key', '=', 'uninstall_simplify_access_management')], limit=1).unlink()

        return res
