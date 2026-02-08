# -*- coding: utf-8 -*-
# This module handles custom access management for Odoo menus.
# It extends the 'ir.ui.menu' model to modify how menus are retrieved based on user access management settings.
# It checks user-specific menu restrictions and hides menus based on defined access rules.
# Odoo Version: 18

from odoo import fields, models, api, _
from odoo.http import request


class IrUiMenu(models.Model):
    _inherit = 'ir.ui.menu'

    @api.model
    def search(self, args, offset=0, limit=None, order=None):
        """
        Overrides the default search method to filter menus based on user access rules
        and company context.
        """
        ids = super(IrUiMenu, self).search(args, offset=offset, limit=limit, order=order)
        user = self.env.user

        try:
            # Retrieve the current company ID from cookies or use the default company
            cids = request.httprequest.cookies.get('cids')
            cids = cids.split(',')[0] if cids else str(self.env.company.id)

            # Filter the menus based on user access rules and company IDs
            for menu_id in user.access_management_ids.filtered(
                    lambda line: int(cids) in line.company_ids.ids
            ).mapped('hide_menu_ids.menu_id'):
                # menu_id = self.browse(menu_id)
                if menu_id in ids:
                    ids = ids - menu_id  # Exclude the menu from the results if restricted

            # Apply offset and limit to the filtered menu list
            if offset:
                ids = ids[offset:]
            if limit:
                ids = ids[:limit]
        except Exception as e:
            # In case of any error (like missing cookies or other issues), we simply pass
            pass

        return ids

    @api.model_create_multi
    def create(self, vals_list):
        """
        Overrides the create method to add menu items when a new menu is created.
        A menu item is linked to each new menu record.
        """
        res = super(IrUiMenu, self).create(vals_list)
        menu_item_obj = self.env['menu.item']
        for record in res:
            menu_item_obj.create({'name': record.display_name, 'menu_id': record.id})
        return res

    def unlink(self):
        """
        Overrides the unlink method to delete associated menu items when a menu is deleted.
        """
        menu_item_obj = self.env['menu.item']
        for record in self:
            menu_item_obj.search([('menu_id', '=', record.id)]).unlink()
        return super(IrUiMenu, self).unlink()
