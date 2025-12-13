{
    'name': 'Component Receiving',
    'version': '1.0',
    'author': 'Mohamed said',
    'depends': ['stock', 'product','product_custom_fields','repair_approval'],
    'data': [
        'security/ir.model.access.csv',
        'views/add_field _service_cat_stock_picking.xml',
        'views/stock_picking_logic.xml',
        'views/RO_logic.xml',
        'views/inherit_stock_picking_type.xml',
    ],
    'installable': True,
    'application': True,
}
