{
    'name': "Ejad ERP",
    'version': '15.0.0.1',
    'depends': [
        'base',
        'board',
        'sale_management',

        #'web_islamic_datepicker',

        # 'ejad_ejad_erp_account',
        # 'ejad_erp_purchase',
        # 'ejad_erp_stock',
        # 'ejad_erp_hr',
        #'ejad_erp_backend_theme',
    ],
    'author': "CVC",
    'website': "http://www.cvc-sa.com/",
    'description': """
    """,
    'data': [
        'security/security_groups.xml',
        'views/login_layout.xml',
        'views/preference_view.xml',
        # 'js.xml',
    ],
    "assets": {"web.assets_backend": ["ejad_erp_base/static/src/js/base.js"]
     },
    "qweb": [
        'static/src/xml/layout.xml',
    ],
    'application': True,
}
