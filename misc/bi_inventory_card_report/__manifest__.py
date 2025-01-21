# -*- coding: utf-8 -*-
# Part of Browseinfo. See LICENSE file for full copyright and licensing details.

{
    "name" : "Inventory Stock Card Report",
    "version" : "15.0.0.0",
    "category" : "Inventory",
    'summary': 'Print stock card report in xls stock movement pdf report stock card excel report inventory stock card report by product stock card report stock inventory report product movement report product stock inventory report stock report warehouse report',
    "description": """Stock Card Report odoo app offers a comprehensive and detailed stock card report that provides an overview for in and out stock movements with quantities. User can generate stock card report for specific time period by selecting start and end dates, also generate a report for individual products or product categories filtered by warehouse or stock location.""",
    "author": "BrowseInfo",
    "website" : "https://www.browseinfo.com",
    "price": 25,
    "currency": 'EUR',
    "depends" : ['base','sale_management','stock','purchase'],
    "data": [
            'security/ir.model.access.csv',
            'report/inventory_card_report.xml',
            'report/inventory_card_report_template.xml',
            'views/excel_report.xml',
            'wizard/inventory_card_report_view.xml',
            ],
    'qweb': [],
    "auto_install": False,
    "installable": True,
    'license': 'OPL-1',
    'live_test_url':"https://youtu.be/uKXlnA18v_0",
    "images":['static/description/Inventory-Stock-Card-Report-Banner.gif'],
}
