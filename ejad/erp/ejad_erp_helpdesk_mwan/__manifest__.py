# -*- coding: utf-8 -*-
{
    'name': "Ejad Erp Helpdesk Mwan",
    'description': """""",
    'category': 'Operations/Helpdesk',
    'version': '15.0.0.0.1',
    'depends': ['base', 'website', 'helpdesk', 'website_helpdesk_form', 'ejad_erp_helpdesk','purchase'],
    'data': [
        'security/ir.model.access.csv',
        'security/helpdesk_teams_security.xml',
        # 'security/group_user.xml',
        'views/helpdesk_team_inh.xml',
        'views/helpdesk_ticket_inh.xml',
        'views/res_partner.xml',
        'wizards/convert_team.xml',
        'views/helpdesk_ticket.xml',
        'views/website_menu.xml',
        'views/helpdesk_templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            '/ejad_erp_helpdesk/static/src/validation/dist/jquery.validate.js',
            '/ejad_erp_helpdesk_mwan/static/src/js/custom.js',
        ],
    },
    'installable': True,
    'auto_install': False,
}
