# -*- coding: utf-8 -*-
{
    'name': 'Azbah Custom Invoice Templates',
    'version': '15.1',
    'summary': 'Custom Templates for Azbah Invoices',
    'description': "",
    'depends': ['base', 'account_accountant', 'web', 'account', 'sale'],
    'data': [
        'report/customer_invoice.xml',
        'report/payment_receipt.xml',
        'report/journal_entry.xml',
    ],

    'assets': {
        'web.assets_common': [
            'custom_invoice_templates/static/src/css/invoice_styles.css',
            'custom_invoice_templates/static/src/fonts/*.ttf',
        ],
        'web.assets_qweb': [
            'custom_invoice_templates/static/src/css/invoice_styles.css',
        ],
        'web.assets_backend': [
            'custom_invoice_templates/static/src/css/invoice_styles.css'
        ],
        'web.assets_frontend': [
            'custom_invoice_templates/static/src/css/invoice_styles.css'
        ],
        'web.report_assets_common': [
            'custom_invoice_templates/static/src/css/invoice_styles.css',
        ],
    }

}
