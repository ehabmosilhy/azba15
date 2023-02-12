{
    "name": "Azbah - Accounting",
    "version": "15.1",
    "license": "LGPL-3",
    "category": "accounting",
    "depends": ["base", "account_accountant"],
    "data": [
        'payments/account_payment_view.xml',
        'payments/batch_vendor_bill.xml',
        'auto_reconcile/res_partner.xml',
        'security/account_batch_bill.xml'

    ],
    'assets': {
        'web.assets_backend': [
            'azbah_accounting/static/src/js/*.js',
        ], }
}
