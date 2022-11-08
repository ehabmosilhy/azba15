{
    "name": "Azbah - POS Changes",
    "version": "15.1",
    "license": "LGPL-3",
    "category": "POS Changes for Azba",
    "depends": ["base", "point_of_sale"],
    "data": [
        "views/pos_config.xml",
        "security/pos_config_rules.xml"

    ],

'assets': {
        'point_of_sale.assets': [
            'azbah_pos/static/src/js/**/*.js',
        ],
        'web.assets_qweb': [
            'azbah_pos/static/src/xml/**/*.xml',
        ],
    }

}
