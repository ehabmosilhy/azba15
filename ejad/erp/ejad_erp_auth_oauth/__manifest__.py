{
    'name': "Ejad ERP Auth Oauth",
    'version': '15.0.0.1',
    'depends': [
        'base',
        'web',
        'auth_oauth',
        'login_signup_captcha',
    ],
    'external_dependencies': {
        'python': ['pyotp']
    },
    'author': "EjadTech",
    'website': "http://www.ejadtech.sa/",
    'description': """
    """,
    'data': [
        "data/auth_oauth_data.xml",
        "views/auth_oauth_views.xml",
        "views/res_config_settings_views.xml",
        # "views/auth_oauth_templates.xml",
        # "views/web_login.xml",
        "views/otp_templates.xml",
    ],
    "qweb": [
    ],
    'assets': {
        'web.assets_frontend': [
            '/ejad_erp_auth_oauth/static/src/scss/auth_oauth.scss',
            '/ejad_erp_auth_oauth/static/src/validation/dist/jquery.validate.js',
            # '/ejad_erp_auth_oauth/static/src/js/ejad_auth_sms_login.js',
            '/ejad_erp_auth_oauth/static/src/js/ejad_auth_view.js',
        ],
    },
    'application': True,
}
