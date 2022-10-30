# -*- coding: utf-8 -*-

{
    'name': 'Ejad ERP Helpdesk',
    'version': '15.0.0.0',
    'category': 'Operations/Helpdesk',
    "sequence": 1,
    "description": """""",
    "depends": ['base', 'website', 'helpdesk', 'website_helpdesk_form', 'hr', 'theme_scita'],
    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',
        'security/ticket_security.xml',
        # 'data/stages.xml',
        'wizard/refuse_reason.xml',
        'wizard/return_reason.xml',
        'view/hr_department_view.xml',
        'view/helpdesk_views.xml',
        'view/helpdesk_type_views.xml',
        'view/help_desk_templates.xml',
        'view/pes_partner_inh.xml',
        'view/website_menu.xml'
    ],
    'assets': {
        'web.assets_frontend': [
            '/ejad_erp_helpdesk/static/src/scss/custom.scss',
            '/ejad_erp_helpdesk/static/src/js/sub_ticket_type.js',
        ],
    },
    'installable': True,
    'auto_install': False,

}
