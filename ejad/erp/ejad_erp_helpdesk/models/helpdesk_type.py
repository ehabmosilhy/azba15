# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.addons.helpdesk.models.helpdesk_ticket import HelpdeskTicket as HDT
from odoo.http import request


class HelpdeskTicketTypeLine(models.Model):
    _name = 'helpdesk.ticket.type.line'

    name = fields.Char(string="Sub Ticket Type", translate=True)
    ticket_type_id = fields.Many2one('helpdesk.ticket.type', string="Parent Ticket Type", ondelete='cascade')

    _sql_constraints = [
        ('name_uniq', 'unique (name,ticket_type_id)', "Type name already exists in the same parent ticket type !"),
    ]


class HelpdeskTicketType(models.Model):
    _inherit = 'helpdesk.ticket.type'

    ticket_type_line_ids = fields.One2many('helpdesk.ticket.type.line', 'ticket_type_id')
    helpdesk_team_id = fields.Many2one('helpdesk.team', string="Helpdesk Team")


class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    ticket_type_line_id = fields.Many2one('helpdesk.ticket.type.line', string="Sub Type Task", tracking=True)
    mobile = fields.Char(string="Customer Mobile", tracking=True)
    personal_id = fields.Char(string="Personal ID", tracking=True)

    def _default_team_id(self):
        team_id = self.env['helpdesk.team'].search([('member_ids', 'in', self.env.uid)], limit=1).id
        if not team_id:
            team_id = self.env['helpdesk.team'].search([], limit=1).id
        return team_id

    team_id = fields.Many2one('helpdesk.team', string='Helpdesk Team', default=_default_team_id, index=True, tracking=True)
    # partner_email = fields.Char(string='Customer Email', related="partner_id.email", store=True)

    # @api.model_create_multi
    # def create(self, list_value):
    #     for vals in list_value:
    #         # for create ticket with new partner
    #         if not vals.get('partner_id', False):
    #             tickets = super(HelpdeskTicket, self).create(list_value)
    #             for ticket in tickets:
    #                 if ticket.partner_id.email == vals.get('partner_email', False):
    #                     # to overwrite find_or_create in super method that match by email
    #                     check_partner = self.env['res.partner'].find_or_create(
    #                         tools.formataddr((vals.get('partner_name'), vals.get('partner_email')))
    #                     )
    #                     if check_partner: # there is match by email
    #                         new_partner = self.env['res.partner'].create({'name': vals.get('partner_name'),
    #                                                                       'email': vals.get('partner_email'),
    #                                                                       'mobile': vals.get('mobile'),
    #                                                                       'personal_id': vals.get('personal_id')})
    #                         # update ticket with new partner
    #                         ticket.write({'partner_id': new_partner.id,
    #                                       'mobile': new_partner.mobile,
    #                                       'personal_id': new_partner.personal_id,
    #                                       'partner_email': new_partner.email})
    #                     else:
    #                         ticket.partner_id.write({'mobile': vals.get('mobile', False), 'personal_id': vals.get('personal_id', False)})
    #         # for create ticket with partner already exist
    #         else:
    #             tickets = super(HelpdeskTicket, self).create(list_value)
    #             for ticket in tickets:
    #                 # if ticket.partner_id.email == vals.get('partner_email', False):
    #                 ticket.write({'mobile': ticket.partner_id.mobile,
    #                               'personal_id': ticket.partner_id.personal_id,
    #                               'partner_email': ticket.partner_id.email})
    #         return tickets

    @api.model_create_multi
    def create(self, list_value):
        print("created ticket from NEW")
        now = fields.Datetime.now()
        # determine user_id and stage_id if not given. Done in batch.
        teams = self.env['helpdesk.team'].browse([vals['team_id'] for vals in list_value if vals.get('team_id')])
        team_default_map = dict.fromkeys(teams.ids, dict())
        for team in teams:
            team_default_map[team.id] = {
                'stage_id': team._determine_stage()[team.id].id,
                'user_id': team._determine_user_to_assign()[team.id].id
            }

        # Manually create a partner now since 'generate_recipients' doesn't keep the name. This is
        # to avoid intrusive changes in the 'mail' module
        for vals in list_value:
           # partner_frontend_lang = request and request.lang.code
            partner_frontend_lang = self.env.user.partner_id.lang
            default_lang = self.env.context.get('lang')
            partner_id = vals.get('partner_id', False)
            partner_name = vals.get('partner_name', False)
            partner_email = vals.get('partner_email', False)
            if partner_name and partner_email and not partner_id:
                print("vals = ", vals)
                if not vals.get('entity_type', False):
                    vals['partner_id'] = self.env['res.partner'].create({
                        'name': partner_name,
                        'email': partner_email,
                        'mobile': vals.get('mobile', False),
                        'personal_id': vals.get('personal_id', False),
                        'lang': partner_frontend_lang or default_lang,
                    }).id
                else:
                    print('create new partner')
                    if vals.get('entity_type', False) == 'person':
                        vals['partner_id'] = self.env['res.partner'].create({
                            'name': partner_name,
                            'email': partner_email,
                            'mobile': vals.get('partner_mobile', False),
                            'personal_id': vals.get('personal_id', False),
                            'lang': partner_frontend_lang or default_lang,
                        }).id
                    elif vals.get('entity_type', False) == 'company':
                        vals['partner_id'] = self.env['res.partner'].create({
                            'name': partner_name,
                            'tax_reg_no': vals.get('tax_reg_no', False),
                            'commercial_reg_no': vals.get('commercial_reg_no', False),
                            'is_company': True,
                            'lang': partner_frontend_lang or default_lang,
                        }).id
                    elif vals.get('entity_type', False) == 'public_sector':
                        vals['partner_id'] = self.env['res.partner'].create({
                            'name': partner_name,
                            'email': partner_email,
                            'mobile': vals.get('partner_mobile', False),
                            'lang': partner_frontend_lang or default_lang,
                        }).id
            else:
                exist_partner = self.env['res.partner'].browse(vals.get('partner_id', False))
                #print("exist_partner", exist_partner)
                if not vals.get('entity_type', False):
                        vals['partner_email'] = exist_partner.email
                        vals['mobile'] = exist_partner.mobile
                        vals['personal_id'] = exist_partner.personal_id
                else:
                    if vals.get('entity_type', False) == 'person':
                        vals['partner_email'] = exist_partner.email
                        if not exist_partner.mobile:
                            exist_partner.mobile = vals.get('partner_mobile', False)
                        else:
                            vals['mobile'] = exist_partner.mobile

                        if not exist_partner.personal_id:
                            exist_partner.personal_id = vals.get('personal_id', False)
                        vals['personal_id'] = exist_partner.personal_id
                        exist_partner.lang = partner_frontend_lang or default_lang
                    elif vals.get('entity_type', False) == 'company':
                        print("founded company")
                        vals['tax_reg_no'] = exist_partner.tax_reg_no
                        if not exist_partner.commercial_reg_no:
                            exist_partner.commercial_reg_no = vals.get('commercial_reg_no', False)
                        vals['commercial_reg_no'] = exist_partner.commercial_reg_no
                        vals['partner_email'] = exist_partner.email
                        exist_partner.lang = partner_frontend_lang or default_lang
                    elif vals.get('entity_type', False) == 'public_sector':
                        vals['partner_email'] = exist_partner.email
                        if not exist_partner.mobile:
                            exist_partner.mobile = vals.get('partner_mobile', False)
                        else:
                            vals['mobile'] = exist_partner.mobile
                        exist_partner.lang = partner_frontend_lang or default_lang

        # determine partner email for ticket with partner but no email given
        partners = self.env['res.partner'].browse([vals['partner_id'] for vals in list_value if
                                                   'partner_id' in vals and vals.get(
                                                       'partner_id') and 'partner_email' not in vals])
        partner_email_map = {partner.id: partner.email for partner in partners}
        partner_name_map = {partner.id: partner.name for partner in partners}

        for vals in list_value:
            if vals.get('team_id'):
                team_default = team_default_map[vals['team_id']]
                if 'stage_id' not in vals:
                    vals['stage_id'] = team_default['stage_id']
                # Note: this will break the randomly distributed user assignment. Indeed, it will be too difficult to
                # equally assigned user when creating ticket in batch, as it requires to search after the last assigned
                # after every ticket creation, which is not very performant. We decided to not cover this user case.
                if 'user_id' not in vals:
                    vals['user_id'] = team_default['user_id']
                if vals.get(
                        'user_id'):  # if a user is finally assigned, force ticket assign_date and reset assign_hours
                    vals['assign_date'] = fields.Datetime.now()
                    vals['assign_hours'] = 0
            # set partner email if in map of not given
            if vals.get('partner_id') in partner_email_map:
                vals['partner_email'] = partner_email_map.get(vals['partner_id'])
            # set partner name if in map of not given
            if vals.get('partner_id') in partner_name_map:
                vals['partner_name'] = partner_name_map.get(vals['partner_id'])

            if vals.get('stage_id'):
                vals['date_last_stage_update'] = now

        # context: no_log, because subtype already handle this
        tickets = super(HDT, self).create(list_value)

        # make customer follower
        for ticket in tickets:
            if ticket.partner_id:
                ticket.message_subscribe(partner_ids=ticket.partner_id.ids)

            ticket._portal_ensure_token()

        # apply SLA
        tickets.sudo()._sla_apply()

        return tickets