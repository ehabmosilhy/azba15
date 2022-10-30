{
    'name': 'Ejad Web Widget Digitized Signature',
    'version': '15.0.1.0.0',
    'category': 'Web',
    'depends': [
        'web',
        'mail',
    ],
    'data': [
        # 'views/web_digital_sign_view.xml',
        'views/res_users_view.xml',
    ],
    'assets': {
        'web.assets_backend': [
             '/web_widget_digitized_signature/static/src/js/digital_sign.js',
        ],
        'web.assets_qweb': [
            '/web_widget_digitized_signature/static/src/xml/digital_sign.xml',
        ],
    },
    'installable': True,
    'development_status': 'Production/Stable',
    'maintainers': ['mgosai'],
}
