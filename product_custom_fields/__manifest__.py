{
    'name': 'Product Custom Fields',
    'version': '1.0',
    'author': 'Mohamed Said',
    'category': 'Product',
    'license': 'LGPL-3',
    'depends': ['product', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'views/product_form_view.xml',
        'views/product_spare_tab_view.xml',
    ],
    'installable': True,
    'application': True,
}
