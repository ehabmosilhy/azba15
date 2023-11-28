# -*- coding: utf-8 -*-

{
    'name': 'AZ Partner Ledger with Partner Filter',
    'version': '15.0.1.0.1',
    'summary': """Azbah Partner Ledger Report with Partner Filter""",
    'description': """Partner Ledger Report with Partner Filter""",
    'category': 'Accounting',
    'depends': ['account'],
    'data': [
        'views/partner_ledger.xml',
        'report/report_partner_ledger.xml',
        'views/report.xml',
        'wizard/account_report_general_ledger_view.xml',
        'security/ir.model.access.csv',
    ],
    'images': ['static/description/banner.png'],
    'license': 'LGPL-3',
    'installable': True,
    'application': False
}
