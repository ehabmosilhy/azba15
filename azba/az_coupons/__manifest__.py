{
    "name": "AZ - Coupons",
    "version": "15.0.1.0",
    "license": "LGPL-3",
    "category": "Sales",
    "depends": ["base",
                "stock_account",
                'mail',
                'base_setup',
                'contacts','pos_coupon',
                "point_of_sale","stock"],
    "data": [
        'views/coupon_coupon.xml',
        'views/res_config_settings.xml',
        # 'views/res_partner.xml',
        'security/ir.model.access.csv',
    ],

    'assets': {
        'point_of_sale.assets': [
            'az_coupons/static/src/js/**/*.js',
            'az_coupons/static/src/xml/**/*.xml',
        ], },
    "installable": True,
    "auto_install": False,
}