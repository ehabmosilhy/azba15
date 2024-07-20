{
    "name": "AZ - Coupons",
    "version": "15.0.1.0",
    "license": "LGPL-3",
    "category": "Sales",
    "depends": ["point_of_sale", "pos_coupon"],
    "data": [
        'views/coupon_coupon.xml',
        'views/product_template.xml',
        'security/ir.model.access.csv',
    ],

    'assets': {
        'point_of_sale.assets': [
            'az_coupons/static/src/js/**/*.js',
        ], },
    "installable": True,
    "auto_install": False,
}