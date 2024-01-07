# -*- coding: utf-8 -*-

{
    'name': 'POS Serial Number Validator',
    'version': '15.0.1.0.0',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'category': 'Point of Sale',
    'summary': """Validate Serial number of a product by checking availability in stock""",
    'description': """Validate Serial number of a product by checking availability in stock""",
    'depends': ['point_of_sale'],
    'assets': {
        "point_of_sale.assets": [
            "az_pos_traceability_validation/static/src/js/**/*.js",
        ],
    },
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
}