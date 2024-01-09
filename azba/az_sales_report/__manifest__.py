# -*- coding: utf-8 -*-

{
    "name" : "AZ Sales Report",
    "version" : "15.0.0.0",
    "category" : "Sales",
    'summary': 'Sales Report by Product',
    "description": """Sales Report by Product""",
    "author": "Ehab Mosilhy",
    "depends" : ['base','sale_management'],
    "data": [
        'security/ir.model.access.csv',
        'report/sales_report.xml',
        'report/sales_report_template.xml',
        'wizard/sales_report_view.xml',
            ],
}
