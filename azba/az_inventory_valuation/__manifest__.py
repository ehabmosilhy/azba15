{
    'name': 'AZ - Inventory Valuation at Date',
    'version': '15.0.1.0.0',
    'category': 'Inventory',
    'summary': 'Wizard to get stock valuation as of a specific date',
    'depends': ['stock', 'purchase'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/stock_valuation.xml',
        'wizard/product_balance_wizard.xml'
    ],
    'installable': True,

    'installable': True,

    'application': False,
}
