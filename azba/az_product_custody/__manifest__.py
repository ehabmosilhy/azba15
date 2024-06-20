# -*- coding: utf-8 -*-
{
    'name': "Product Custody",
    'summary': "Manage custody products",
    'description': "Module to manage custody products.",
    'author': "Ehab",
    'category': 'Inventory',
    'version': '0.1',
    'depends': ['base', 'stock' ],
    'data': [
        'views/product_custody.xml',
        'views/stock_picking.xml',
        'reports/custody_report.xml',
        'reports/custody_report_template.xml',
        'wizards/custody_report_wizard.xml',
        'security/ir.model.access.csv',
    ],
}
