{
    "name": "Azbah - Accounting - Reports",
    "version": "15",
    "license": "LGPL-3",
    "category": "accounting",
    "depends": ["base", "account_accountant", "account_reports"],
    'assets': {
        'account_reports.assets_financial_report': [
            'az_account_reports/static/src/scss/account_financial_report.scss',
            'az_account_reports/static/src/scss/account_report_print.scss',
        ]},
    "data": [
        # 'security/ir.model.access.csv',
        'wizard/ledger_report_view.xml',
        'report/ledger_report.xml',
        'report/ledger_report_template.xml',
    ],
}
