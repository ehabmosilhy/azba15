{
    'name': 'Partner Credit Limit',
    'version': '1.0',
    'category': 'Sales',
    'summary': 'Set credit limits for partners based on categories',
    'depends': ['base', 'sale', 'point_of_sale'],
    'data': [
        'views/res_partner.xml',
        'security/ir.model.access.csv',
        'views/credit_limit_category.xml',
    ],

    'assets': {
        'point_of_sale.assets': [
            'az_sales_credit_limit/static/src/js/**/*.js',
        ],
    },
    'installable': True,
    'auto_install': False,
}
