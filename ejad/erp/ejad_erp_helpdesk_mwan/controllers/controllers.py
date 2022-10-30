# -*- coding: utf-8 -*-
# from odoo import http
import re
from odoo import http
from odoo.http import request
from odoo.addons.website.controllers.form import WebsiteForm



class WebsiteHelpdesk(http.Controller):
    # pass values of ticket_type ans sub_ticket_type from tickettype (1st) form to helpdesk_ticket_form (2nd)
    @http.route(['/mwan_contactus'], type='http', auth="public", website=True)
    def mwan_contactus_team(self, team=None, **kwargs):
        default_values = {}
        team = http.request.env['helpdesk.team'].sudo().search(
            [('id', '=', request.env.ref('helpdesk.helpdesk_team1').id)], limit=1)
        ticket_types = request.env['helpdesk.ticket.type'].sudo().search([('helpdesk_team_id', '=', team.id)])
        default_values.update({'ticket_types': ticket_types})
        return request.render("ejad_erp_helpdesk_mwan.contactus", {'team': team, 'default_values': default_values})

    # pass values of contactus form (1st) to personal_company_form_ticket (2nd)
    @http.route(['/contactus_type/submit'], type='http', methods=['POST'], auth="public", website=True)
    def mwan_contactus_person_company(self, team=None, **kwargs):
        default_values = {}
        team_id = kwargs.get('team_id', False)
        ticket_type_id = kwargs.get('ticket_type_id', False)
        ticket_type_line_id = kwargs.get('ticket_type_line_id', False)
        entity_type = kwargs.get('entity_type', False)
        partner_name = False
        print("team_id = ", team_id)
        print("ticket_type_id = ", ticket_type_id)
        print("ticket_type_line_id = ", ticket_type_line_id)
        print("entity_type = ", entity_type)
        if team_id:
            team = http.request.env['helpdesk.team'].sudo().search([('id', '=', int(team_id))], limit=1)
            default_values.update({'team': team})
        if ticket_type_id:
            ticket_type = http.request.env['helpdesk.ticket.type'].sudo().search([('id', '=', int(ticket_type_id))])
            default_values.update({'ticket_type': ticket_type})
        if ticket_type_line_id:
            ticket_type_line = http.request.env['helpdesk.ticket.type.line'].sudo().search(
                [('id', '=', int(ticket_type_line_id))])
            default_values.update({'ticket_type_line': ticket_type_line})
        if entity_type:
            default_values.update({'entity_type': entity_type})
        print("default_values = ", default_values)
        partner_id = request.env.user.partner_id
        public_partner = request.env.ref('base.public_partner')
        if partner_id.id != public_partner.id:
            partner_name = partner_id.name
        else:
            partner_name = False
        default_values.update(
            {'partner_name': partner_name, 'partner_email': partner_id.email, 'personal_id': partner_id.personal_id,
             'partner_mobile': partner_id.mobile})
        return request.render("ejad_erp_helpdesk_mwan.contactus_send_ticket1",
                              {'team': team, 'default_values': default_values})

    def get_helpdesk_team_data(self, team, search=None):
        return {'team': team}

    @http.route(['/helpdesk/', '/helpdesk/<model("helpdesk.team"):team>'], type='http', auth="public", website=True)
    def website_helpdesk_teams(self, team=None, **kwargs):
        search = kwargs.get('search')
        print('teamnnnnnnnns')
        # For breadcrumb index: get all team
        teams = request.env['helpdesk.team'].sudo().search(
            ['|', '|', ('use_website_helpdesk_form', '=', True), ('use_website_helpdesk_forum', '=', True),
             ('use_website_helpdesk_slides', '=', True)], order="id asc")

        # if not request.env.user.has_group('helpdesk.group_helpdesk_manager'):
        #     teams = teams.filtered(lambda team: team.website_published)
        if not teams:
            return request.render("website_helpdesk.not_published_any_team")
        result = self.get_helpdesk_team_data(team or teams[0], search=search)
        print(result)
        # For breadcrumb index: get all team
        result['teams'] = teams
        return request.render("website_helpdesk.team", result)


class SubTicketType(http.Controller):
    @http.route(['/subtickettype'], type='json', auth="public", methods=['POST'], website=True)
    def domain_sub_type_ticket(self, ticket_type_id, **kw):
        print("json ticket_type_id", ticket_type_id)
        datas = []
        if ticket_type_id:
            sub_ticket_types = http.request.env['helpdesk.ticket.type.line'].sudo().search(
                [('ticket_type_id', '=', int(ticket_type_id))])
            if sub_ticket_types:
                for sub in sub_ticket_types:
                    dic = {}
                    dic.update({sub.id: sub.name})
                    datas.append(dic)
        return datas


class WebsiteForm(WebsiteForm):

    # @http.route('/website_form/<string:model_name>', type='http', auth="public", methods=['POST'], website=True)
    @http.route('/website/form/<string:model_name>', type='http', auth="public", methods=['POST'], website=True, csrf=False)
    def website_form(self, model_name, **kwargs):
        if request.params.get('personal_id') or request.params.get('mobile') and request.params.get(
                'entity_type') and request.params.get('entity_type') == 'person':
            print("entity_type search entity")
            partner = request.env['res.partner'].sudo().search(
                ['|',('personal_id', '=', kwargs.get('personal_id')), ('mobile', '=', kwargs.get('mobile'))], limit=1)
            print("CU_partner = ", partner)
            print("CU_partner = ", kwargs.get('mobile'))
            print("CU_partner = ", kwargs.get('personal_id'))
            if partner:
                request.params['partner_id'] = partner.id
        if request.params.get('tax_reg_no') or request.params.get('commercial_reg_no') and request.params.get(
                'entity_type') and request.params.get('entity_type') == 'company':
            print("entity_type search entity")
            partner = request.env['res.partner'].sudo().search(
                ['|',('tax_reg_no', '=', kwargs.get('tax_reg_no')),
                 ('commercial_reg_no', '=', kwargs.get('commercial_reg_no')), ('is_company', '=', True)], limit=1)
            print("CU_partner = ", partner)
            if partner:
                request.params['partner_id'] = partner.id

        if request.params.get('partner_email') or request.params.get('partner_mobile') and request.params.get(
                'entity_type') and request.params.get('entity_type') == 'public_sector':
            partner = request.env['res.partner'].sudo().search(
                ['|',('email', '=', kwargs.get('partner_email')),
                 ('mobile', '=', kwargs.get('partner_mobile'))], limit=1)
            if partner:
                request.params['partner_id'] = partner.id

        return super(WebsiteForm, self).website_form(model_name, **kwargs)