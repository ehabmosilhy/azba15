{
    "name": "AZ-Accounting - Batch Purchase ",
    "version": "15",
    "license": "LGPL-3",
    "category": "accounting",
    "depends": ["account", "purchase"]
    , "data": [
    'views/account_move.xml',
    'views/batch_purchase.xml',
    'views/purchase_order.xml',
    'views/stock.xml',
    'report/batch_purchase.xml',
    'report/batch_purchase_template.xml',
    'security/batch_purchase.xml',

    # Sarf Moshtarayat صرف مشتريات
    'views/sarf_moshtarayat/batch_purchase.xml',

]
}
