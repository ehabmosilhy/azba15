{
    "name": "Azbah - Accounting",
    "version": "15.1",
    "license": "LGPL-3",
    "category": "accounting",
    "depends": ["base", "account_accountant"],
    "data": [
        'payments/account_payment_view.xml',
        'batch_purchase/account_batch_purchase.xml',
        'auto_reconcile/res_partner.xml',
        'security/account_batch_purchase.xml'

    ],
    'assets': {
        'web.assets_backend': [
            'azbah_accounting/static/src/js/*.js',
        ], }
}
