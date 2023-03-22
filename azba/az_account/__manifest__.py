{
    "name": "AZ-Accounting",
    "version": "15",
    "license": "LGPL-3",
    "category": "accounting",
    "depends": ["base", "account_accountant"],
    "data": [
        'batch_purchase/batch_purchase.xml',
        'auto_reconcile/res_partner.xml',
        'batch_purchase/purchase_order.xml',
        'batch_purchase/account_move.xml',
        'batch_purchase/stock.xml',
        'security/batch_purchase.xml',
        'payments/account_payment_view.xml',
        'batch_purchase/report/batch_purchase_template.xml',
        'batch_purchase/report/batch_purchase.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'azbah_accounting/static/src/js/*.js',
        ], }

    , 'application': True,
}
