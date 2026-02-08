# -*- coding: utf-8 -*-
# This module extends the 'ir.actions.actions' model to create corresponding records in the 'action.data' model
# when actions are created or deleted. It ensures that related data is properly maintained when action records
# are created or removed.
# Odoo Version: 18

from odoo import api, fields, models, tools


class IrActionsActions(models.Model):
    _inherit = 'ir.actions.actions'

    @api.model_create_multi
    def create(self, vals_list):
        """
        Overrides the create method to create corresponding records in the 'action.data' model
        whenever an action is created.
        """
        res = super(IrActionsActions, self).create(vals_list)
        action_data_obj = self.env['action.data']

        # Creating related records in the 'action.data' model
        for record in res:
            action_data_obj.create({
                'name': record.name,
                'action_id': record.id
            })
        return res

    def unlink(self):
        """
        Overrides the unlink method to remove related 'action.data' records
        whenever an action is deleted.
        """
        action_data_obj = self.env['action.data']

        # Deleting related records in the 'action.data' model
        for record in self:
            action_data_obj.search([('action_id', '=', record.id)]).unlink()

        return super(IrActionsActions, self).unlink()
