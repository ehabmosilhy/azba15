{
    "name": "AZ-Invnetory",
    "description": """Reporting for inventory
    - Creating Report for Product History including initial balance
    """,
    "author": "Azba",
    "version": "15",
    "license": "LGPL-3",
    "category": "stock",
    "depends": ["stock"]
    , "data": [
    'security/ir.model.access.csv',
    'report/product_history_report.xml',
    'wizard/product_history_wizard_view.xml'
]
}
