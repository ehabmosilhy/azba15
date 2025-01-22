{
    'name': 'AZBA Payroll Extensions',
    'version': '15.0.1.0.0',
    'category': 'Human Resources/Payroll',
    'summary': 'Extends HR Payroll functionality',
    'description': """
        Extends HR Payroll functionality with:
        - Employee code in payslip employee selection
        - Excel report generation for payslips
    """,
    'depends': [
        'hr_payroll',
        'report_xlsx_helper',
    ],
    'data': [
        'views/hr_payslip_views.xml',
        'views/report_actions.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
