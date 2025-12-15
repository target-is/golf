{
    'name': 'Repair Approval Lines',
    'version': '1.0',
    'depends': ['repair','sales_team'],
    'data': [
        'security/ir.model.access.csv',
        'views/repair_approval_views.xml',
        'views/wizards_repair_order_buttons.xml',
        'views/repair_cancel_wizard_view.xml',
        'views/modify_cancel_button_repair.xml',
    ],
    'installable': True,
    'application': True
}