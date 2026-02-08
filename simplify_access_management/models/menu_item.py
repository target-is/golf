# -*- coding: utf-8 -*-
# This model manages custom menu items, potentially linking to Odoo's built-in menus (ir.ui.menu).
# It provides a structure for defining menus and their relationships (parent-child) within the system.
from odoo import api, fields, models

class MenuItem(models.Model):
    _name = 'menu.item'
    _description = "Menu Item"

    name = fields.Char('Menu', required=True)
    menu_id = fields.Many2one('ir.ui.menu', string='Parent Menu', help="Reference to the parent menu item.", ondelete='cascade')