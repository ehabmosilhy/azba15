# -*- coding: utf-8 -*-
{
    'name': 'Azbah Custom Invoice Templates',
    'version': '15.1',
    'summary': 'Custom Templates for Azbah Invoices',
    'description': "",
    'depends': ['base', 'account_accountant', 'web',  'account','sale'],
    'data': [
        'report/customer_invoice.xml',
        'report/payment_receipt.xml',
        'report/sanad_template.xml',
    ],

    'assets': {
        'web.assets_common': [
            'custom_invoice_templates/static/src/css/*.css',
            'custom_invoice_templates/static/src/fonts/*.ttf',
        ],
    }
}
