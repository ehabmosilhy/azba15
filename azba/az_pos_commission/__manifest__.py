# -*- coding: utf-8 -*-
{
    'name': "POS Commission",
    'summary': "POS Commission Wizard",
    'description': "POS Commission Wizard.",
    'author': "Ehab",
    'category': 'pos',
    'version': '0.1',
    'depends': ['base', 'point_of_sale'],
    'data': [
        'views/product_template.xml',
        'wizards/pos_commission_wizard.xml',
        'reports/commission_report.xml',
        'reports/commission_report_template.xml',
        'security/ir.model.access.csv',
    ],
}
