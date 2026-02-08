# -*- coding: utf-8 -*-
# This class manages Chatter rights for different models, allowing for fine-grained control
# over which elements (e.g., Chatter, Send Message, Log Notes, Schedule Activity)
# are visible or hidden for specific users based on the selected model and access management.
from odoo import fields, models, api, _
from lxml import etree

class HideChatter(models.Model):
    _name = 'hide.chatter'
    _description = "Chatter Rights"

    access_management_id = fields.Many2one('access.management', 'Access Management')
    model_id = fields.Many2one('ir.model', 'Model')

    hide_chatter = fields.Boolean('Chatter', help="The Chatter will be hidden in selected model from the specified users.")
    hide_send_mail = fields.Boolean('Send Message', help="The Send Message button will be hidden in chatter of selected model from the specified users.")
    hide_log_notes = fields.Boolean('Log Notes', help="The Log Notes button will be hidden in chatter of selected model from the specified users.")
    hide_schedule_activity = fields.Boolean('Schedule Activity', help="The Schedule Activity button will be hidden in chatter of selected model from the specified users.")


