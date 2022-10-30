# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import re
from odoo import http ,_
from odoo.http import request
from odoo.addons.website.controllers.form import WebsiteForm as WF
from odoo.addons.backend_online_services_review.controller.helpdesk import WebsiteForm
from odoo.addons.website_helpdesk_form.controller.main import WebsiteForm as WHF

class WebsiteForm(WebsiteForm):

    @http.route('''/helpdesk/<model("helpdesk.team", "[('use_website_helpdesk_form','=',True)]"):team>/submit''', type='http', auth="public", website=True)
    def website_helpdesk_form(self, team, **kwargs):
        res = super(WebsiteForm, self).website_helpdesk_form(team)
        if not team.active or not team.website_published:
            return request.render("website_helpdesk.not_published_any_team")
        default_values = {}
        services = request.env['product.template'].sudo().search([('beneficiaries_ids', '!=', False)])
        default_values.update({'services': services})
        ticket_types = request.env['helpdesk.ticket.type'].sudo().search([('helpdesk_team_id', '=', team.id)])
        sub_ticket_types = request.env['helpdesk.ticket.type.line'].sudo().search([])
        default_values.update({'ticket_types': ticket_types, 'sub_ticket_types': sub_ticket_types})
        # super(WebsiteForm, self).website_helpdesk_form(team)
        return request.render("website_helpdesk_form.ticket_submit_form", {'team': team, 'default_values': default_values})
        # print("default_values_2 = ", default_values)
        # print("res = ", res)
        # return res

    # for saving data in model
    # @http.route('/website_form/<string:model_name>', type='http', auth="public", methods=['POST'], website=True)
    # def website_form(self, model_name, **kwargs):
    #     print("Saving Data")
    #     print("type = ", request.params.get('ticket_type_id'))
    #     if request.params.get('ticket_type_id'):
    #         service = request.env['helpdesk.ticket.type'].sudo().search([('id', '=', int(kwargs.get('ticket_type_id')))])
    #         if service:
    #             request.params['ticket_type_id'] = service.id
    #     return super(WebsiteForm, self).website_form(model_name, **kwargs)


class WebsiteFormSave(WF):
    # @http.route('/website_form/<string:model_name>', type='http', auth="public", methods=['POST'], website=True)
    @http.route('/website/form/<string:model_name>', type='http', auth="public", methods=['POST'], website=True, csrf=False)
    def website_form(self, model_name, **kwargs):
        print("2nd kwargs =", kwargs)
        if request.params.get('ticket_type_id'):
            request.params['ticket_type_id'] = request.params.get('ticket_type_id')

        ####  writing if partner exist
        # if request.params.get('partner_email'):
        #     partner = request.env['res.partner'].sudo().search([('email', '=', kwargs.get('partner_email'))], limit=1)
        #     if partner:
        #         if request.params.get('mobile'):
        #             partner.update({'mobile', kwargs.get('mobile')})



        # if request.params.get('mobile'):
        #     match = re.match('^[0-9]\d{9}$', request.params.get('mobile'))
        #     print("match = ",match)
        #     if not match:
        #         print("hello not match")
        #         default_values = {}
        #         ticket_type_id = kwargs.get('ticket_type_id')
        #         ticket_type_name = http.request.env['helpdesk.ticket.type'].sudo().search(
        #             [('id', '=', int(ticket_type_id))]).name
        #         if kwargs.get('ticket_type_line_id'):
        #             sub_ticket_type_id = kwargs.get('ticket_type_line_id')
        #             sub_ticket_type_name = http.request.env['helpdesk.ticket.type.line'].sudo().search(
        #                 [('id', '=', int(sub_ticket_type_id))]).name
        #             default_values.update({'sub_ticket_type_id': sub_ticket_type_id,
        #                                    'sub_ticket_type_name': sub_ticket_type_name})
        #         default_values.update(
        #             {'ticket_type_id': ticket_type_id, 'ticket_type_name': ticket_type_name})
        #         return request.render("website_helpdesk_form.ticket_submit", {'default_values': default_values})

        # kwargs['partner_email'] = 'khaled@gmail.com'

        kwargs['partner_email'] = request.env.user.partner_id.email
        kwargs['partner_name'] = request.env.user.partner_id.name
        kwargs['personal_id'] = request.env.user.partner_id.personal_id
        kwargs['mobile'] = request.env.user.partner_id.mobile
        print('kwargs',kwargs)
        return super(WebsiteFormSave, self).website_form(model_name, **kwargs)


class SubTicketType(http.Controller):
    @http.route(['/subtickettype'], type='json', auth="public", methods=['POST'], website=True)
    def domain_sub_type_ticket(self, ticket_type_id, **kw):
        print("json ticket_type_id", ticket_type_id)
        datas = []
        if ticket_type_id:
            sub_ticket_types = http.request.env['helpdesk.ticket.type.line'].sudo().search([('ticket_type_id', '=', int(ticket_type_id))])
            if sub_ticket_types:
                for sub in sub_ticket_types:
                    dic = {}
                    dic.update({sub.id: sub.name})
                    datas.append(dic)
        return datas

    # triggered from js file and return if the ticket exist or not
    @http.route(['/check_ticket_exist'], type='json', auth="public", methods=['POST'], website=True)
    def check_ticket_exist(self, ticket_id, **kw):
        print("json ticket_type_id", ticket_id)
        ticket = http.request.env['helpdesk.ticket'].sudo().search([('id', '=', int(ticket_id))])
        if ticket:
            return True
        else:
            return False

# for new template contain TicketType and subTicketType
class WebsiteHelpdesk(http.Controller):
    @http.route(['/helpdesk/<model("helpdesk.team"):team>/tickettype'], type='http', auth="public", website=True)
    def website_helpdesk_teams(self, team=None, **kwargs):
        default_values = {}
        ticket_types = request.env['helpdesk.ticket.type'].sudo().search([('helpdesk_team_id', '=', team.id)])
        default_values.update({'ticket_types': ticket_types})
        return request.render("ejad_erp_helpdesk.translate_team_with_ticket_type", {'team': team, 'default_values': default_values})

    # pass values of ticket_type ans sub_ticket_type from tickettype (1st) form to helpdesk_ticket_form (2nd)
    @http.route(['/helpdesk/submit'], type='http', methods=['POST'], auth="public", website=True)
    def website_helpdesk_newform(self, team=None, **kwargs):
        error = kwargs.get('error',False)
        default_values = {}
        ticket_type_id = kwargs.get('ticket_type_id')
        ticket_type_name = http.request.env['helpdesk.ticket.type'].sudo().search(
            [('id', '=', int(ticket_type_id))]).name
        if kwargs.get('team_id'):
            team = http.request.env['helpdesk.team'].sudo().search([('id', '=', int(kwargs.get('team_id')))])
        if kwargs.get('ticket_type_line_id'):
            sub_ticket_type_id = kwargs.get('ticket_type_line_id')
            sub_ticket_type_name = http.request.env['helpdesk.ticket.type.line'].sudo().search(
                [('id', '=', int(sub_ticket_type_id))]).name
            default_values.update({'sub_ticket_type_id': sub_ticket_type_id,
                                   'sub_ticket_type_name': sub_ticket_type_name})
        services = []
        print("ticket_type_name",ticket_type_name)

        default_values.update({'ticket_type_id': ticket_type_id, 'ticket_type_name': ticket_type_name, 'services': services})
        print("team", team)
        print("default_values", default_values)
        return request.render("website_helpdesk_form.ticket_submit_form", {'error':error,'team': team, 'default_values': default_values})

    # for check phone valid
    # @http.route(['/website_form/'], type='http', methods=['POST'], auth="public", website=True)
    # def website_helpdesk_newform(self, team=None, **kwargs):
    #     print("phone valid", kwargs)


    # to redirect to ticket query page
    @http.route(['/helpdesk/query_ticket'], type='http', auth="public", website=True)
    def website_helpdesk_query_ticket(self, team=None, **kwargs):
        return request.render("ejad_erp_helpdesk.user_query_ticket")

    # to retrieve data from query ticket page (ticket_id , user_mobile)
    @http.route(['/helpdesk/ticket_status'], type='http', methods=['POST'], auth="public", website=True)
    def website_helpdesk_ticket_status(self, team=None, **kwargs):
        ticket_id = kwargs.get('ticket_id')
        mobile = kwargs.get('user_mobile')
        if mobile:
            print("mobile = ", mobile)
            match = re.match('^[0-9]\d{9}$', mobile)
            if not match:
                error_msg = _("your personal ID number or commercial number is not correct")
                return request.render("ejad_erp_helpdesk.user_query_ticket",{'error': error_msg})
            # ticket = http.request.env['helpdesk.ticket'].sudo().search([('id', '=', int(ticket_id)), ('mobile', '=', mobile)])
            ticket = http.request.env['helpdesk.ticket'].sudo().search(['|',('personal_id', '=', mobile),('commercial_reg_no', '=', mobile)])
            if ticket:
                return request.render("ejad_erp_helpdesk.user_query_ticket_status", {'ticket': ticket})
            else:
                return request.render("ejad_erp_helpdesk.user_query_ticket", {'error': _('No Ticket Found with This Number')})


# check if partner exists or not by(personal_id and mobile)
class WebsiteFormPatnerSearch(WHF):
    # @http.route('/website_form/<string:model_name>', type='http', auth="public", methods=['POST'], website=True)
    @http.route('/website/form/<string:model_name>', type='http', auth="public", methods=['POST'], website=True, csrf=False)
    def website_form(self, model_name, **kwargs):
        print("hello Personal_id and Mobile partner search",request.env.ref('base.public_user'))
        public_user = request.env.ref('base.public_user').sudo().partner_id.id
        if request.env.user.partner_id.id == public_user or request.params.get('entity_type') == 'company':
            if request.params.get('partner_email') or request.params.get('mobile'):
                partner = request.env['res.partner'].sudo().search(['|',
                                                                    '&',
                                                                    ('email', '!=', False),
                                                                    ('email', '=', request.params.get('partner_email')),
                                                                    '&',
                                                                    ('mobile', '!=', False),
                                                                    ('mobile', '=', request.params.get('mobile'))
                                                                    ],
                                                                   limit=1)

                partner_id = partner and partner.id or False
                request.params['partner_id'] = partner_id

        else:
            request.params['partner_id'] = request.env.user.partner_id.id
        return super(WHF, self).website_form(model_name, **kwargs)