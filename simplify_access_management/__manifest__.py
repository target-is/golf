# -*- coding: utf-8 -*-
{
    'name': 'Simplify Access Management',
    'version': '1.0',
    'sequence': 5,
    "author": "Mohamed Said , nhm Team",
    'license': 'LGPL-3',
    'category': 'Hidden/Tools',
    'summary': """""",
    'description': """""",
    "images": ["static/description/banner.gif"],
    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',
        'data/view_data.xml',
        'views/access_management_view.xml',
        'views/res_users_view.xml',
        'views/store_model_nodes_view.xml',
    ],
    'assets': {
        'web.assets_backend': [
            '/simplify_access_management/static/src/js/action_menus.js',
            '/simplify_access_management/static/src/js/hide_chatter.js',
            '/simplify_access_management/static/src/js/cog_menu.js',
            '/simplify_access_management/static/src/js/form_controller.js',
            # '/simplify_access_management/static/src/js/PivotHeader.js',
            '/simplify_access_management/static/src/js/model_field_selector.js',
            '/simplify_access_management/static/src/js/search_bar_menu.js',
        ],

    },
    # 'depends': ['web', 'advanced_web_domain_widget', 'account_reports'],
    'depends': ['web', 'advanced_web_domain_widget'],
    'post_init_hook': 'post_install_action_dup_hook',
    'application': True,
    'installable': True,
    'auto_install': False,
}
