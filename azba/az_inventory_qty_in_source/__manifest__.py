{
    'name': 'Stock Move Quantity in Source Location',
    'version': '1.0',
    'category': 'Inventory',
    'summary': 'Adds a computed field to show quantity in source location for stock moves',
    'depends': ['stock'],
    'data': [
        'views/stock_picking.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
