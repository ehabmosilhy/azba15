# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Sitaram Solutions (<https://sitaramsolutions.in/>).
#
#    For Module Support : info@sitaramsolutions.in  or Skype : contact.hiren1188
#
##############################################################################
{
    'name': "Print POS Session Report",
    'version': "15.0.0.0",
    'summary': "",
    'category': 'Point Of Sale',
    "license": "OPL-1",
    'description': """
    """,
    'author': "Sitaram",
    'website':"http://www.sitaramsolutions.in",
    'depends': ['base', 'point_of_sale'],
    'data': [
        'reports/pos_report.xml',
'reports/pos_session_report_template.xml'
    ],
    'demo': [],
    'images':['static/description/banner.png'],
    'live_test_url':'https://youtu.be/xYuOpF4aZis',
    'installable': True,
    'application': False,
    'auto_install': False,
}
