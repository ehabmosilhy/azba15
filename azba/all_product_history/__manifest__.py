# Copyright 2019 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "All Product History Report",
    "summary": "Add all product history report on Inventory Reporting.",
    "version": "15.0.1.0.0",
    "category": "Warehouse",
    "website": "https://github.com/OCA/stock-logistics-reporting",
    "author": "Ecosoft, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "depends": ["stock", "date_range", "report_xlsx_helper"],
    "data": [
        "security/ir.model.access.csv",
        "data/paper_format.xml",
        "data/report_data.xml",
        "reports/all_product_history.xml",
        "wizard/all_product_history_wizard_view.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "all_product_history/static/src/css/**/*",
            "all_product_history/static/src/js/**/*",
        ]
    },
    "installable": True,
}
