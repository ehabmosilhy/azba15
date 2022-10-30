# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import datetime
from dateutil import relativedelta
from odoo import api, fields, models, _
from odoo.addons.helpdesk.models.helpdesk_ticket import TICKET_PRIORITY
from odoo.addons.http_routing.models.ir_http import slug
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression


class HelpdeskStage(models.Model):
    _inherit = 'helpdesk.stage'

    is_refused = fields.Boolean(string='مرحلة رفض')
    prev_stage = fields.Many2one('helpdesk.stage', string='المرحلة السابقة', )
    next_stage = fields.Many2one('helpdesk.stage', string='المرحلة القادمة')

    next_team = fields.Many2one('helpdesk.team', string='الفريق القادم')

    responsible_stage_type = fields.Selection([('position', 'وظيفة'), ('person', 'شخص')], string='نوع المسؤول عن المرحلة')
    positions = fields.Selection([('direct_manager', 'المدير المباشر'),
                                  ('dept_manager', 'مدير الادارة'),
                                  ('agency_manager', 'وكيل الوكالة'),
                                  ('create_user', 'مقدم الطلب'),
                                  ], string='الوظائف')
    responsible_user = fields.Many2one('res.users', string='المسؤول')


class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    is_show_button = fields.Boolean(compute="_show_button", default=False)
    is_prev_allowed = fields.Boolean(compute="_show_button", default=False)
    is_refused = fields.Boolean(compute="_show_button", default=False)

    owner_user = fields.Many2one('res.users', compute="get_owner_user")
    assign_method = fields.Selection(related="team_id.assign_method")

    is_returned = fields.Boolean()
    return_message = fields.Text("Return message", track_visibility="onchange")
    refuse_message = fields.Text("سبب الرفض", track_visibility="onchange")

    prev_ticket = fields.Many2one('helpdesk.ticket', string='التذكرة السابقة', tracking=True)
    replay_partner = fields.Text("Replay to partner", tracking=True)

    def update_user_id(self):
        for rec in self:
            if rec.team_id.assign_method == 'auto':
                rec.user_id = False
                if rec.stage_id.responsible_user:
                    rec.user_id = rec.stage_id.responsible_user.id

                elif rec.stage_id.positions == 'direct_manager':
                    rec.user_id = rec.owner_user.employee_id.parent_id.user_id.id

                elif rec.stage_id.positions == 'dept_manager':
                    if rec.owner_user.employee_id.department_id.type == 'dept':
                        rec.user_id = rec.owner_user.employee_id.department_id.parent_id.manager_id.user_id.id
                    else:
                        rec.user_id = rec.owner_user.employee_id.department_id.manager_id.user_id.id

                elif rec.stage_id.positions == 'agency_manager':
                    dept_obj = rec.env['hr.department']
                    agency_ids = dept_obj.search([("type", "=", 'ean13')])
                    if agency_ids:
                        for agency in agency_ids:
                            child_dept_ids = dept_obj.search([('id', 'child_of', agency.id)])
                            if rec.create_uid.employee_id.department_id.id in child_dept_ids.ids:
                                rec.user_id = agency.manager_id.user_id.id or False
                                break;
                    if not rec.user_id:
                        raise ValidationError(_("يجب تعين وكيل الوكالة"))

                elif rec.stage_id.positions == 'create_user':
                    user = False
                    if rec.partner_id.id:
                        user = self.env['res.users'].search([('partner_id', '=', rec.partner_id.id)], limit=1).id
                    if user:
                        rec.user_id = user
                    else:
                        raise ValidationError(_("يجب انشاء مستخدم لمقدم الطلب"))

    def action_accept(self):
        for rec in self:
            if rec.stage_id.next_stage:
                rec.stage_id = rec.stage_id.next_stage.id
                rec.update_user_id()
                rec.create_activity()

                if rec.stage_id.is_close and rec.stage_id.next_team:
                    self.env['helpdesk.ticket'].create({
                        'name': rec.name,
                        'partner_id': rec.partner_id.id,
                        'partner_email': rec.partner_email,
                        'email_cc': rec.email_cc,
                        'team_id': rec.stage_id.next_team.id,
                        'prev_ticket': rec.id,
                        'ticket_type_id': rec.ticket_type_id.id,
                        'tag_ids': rec.tag_ids.ids,
                        'description': rec.description,
                    })
                    # 'timesheet_ids': rec.timesheet_ids.ids,

    def create_activity(self):
        # create activity
        self = self.sudo()
        if self.user_id:
            self.activity_feedback(['mail.mail_activity_data_todo'], feedback='تم اكمال المهمة بنجاح شكرا لك')
            self.activity_schedule('mail.mail_activity_data_todo', user_id=self.user_id.id, res_id=self.id)

    def action_return(self):
        for rec in self:
            if rec.stage_id.prev_stage:
                rec.stage_id = rec.stage_id.prev_stage.id
                rec.update_user_id()
                rec.create_activity()

    @api.onchange('stage_id')
    def checkAccess(self):
        if self.team_id.privacy == 'invite':
            if int(self.env.user.id) not in self.team_id.visibility_member_ids.ids:
                raise ValidationError('عذرا لا يمكنك تغيير الحالة')


    @api.depends('partner_email')
    def get_owner_user(self):
        for rec in self:
            rec.owner_user = self.env['res.users'].search(['|', ('partner_id', '=', rec.partner_id.id), ('email', '=ilike', rec.partner_email)], limit=1)

    @api.depends('stage_id')
    def _show_button(self):
        self = self.sudo()
        for rec in self:
            rec.ensure_one()
            rec.is_show_button = False
            rec.is_prev_allowed = False
            rec.is_refused = False
            if rec.stage_id.prev_stage:
                rec.is_prev_allowed = True
            if rec.stage_id.is_refused or rec.stage_id.is_close:
                rec.is_refused =True
            if rec.stage_id.responsible_user:
                if not rec.stage_id.is_close and (self.env.user.id == rec.stage_id.responsible_user.id or self.env.user.id in (1,2)):
                    rec.is_show_button = True
            # Direct Manager Stage
            elif rec.stage_id.positions == 'direct_manager':
                if rec.env.user == self.sudo().owner_user.employee_id.parent_id.user_id \
                        or self.user_has_groups('ejad_erp_helpdesk.group_helpdesk_direct_manager') \
                        or (rec.owner_user and self.env.uid == rec.owner_user.id
                            and self.user_has_groups(
                            'ejad_erp_helpdesk.group_helpdesk_itself_direct_manager')):
                    rec.is_show_button = True
            # Department Manager Stage
            elif rec.stage_id.positions == 'dept_manager':
                # dept_manager_user = rec.owner_user.employee_id.department_id.manager_id.user_id
                if self.env.user == rec.user_id or self.user_has_groups('ejad_erp_helpdesk.group_helpdesk_dept_manger'):
                    rec.is_show_button = True
            # Agency Manager Stage
            elif rec.stage_id.positions == 'agency_manager':
                if self.env.user == rec.user_id or self.user_has_groups('ejad_erp_helpdesk.group_helpdesk_agency_manager'):
                    rec.is_show_button = True

            # create request user Stage
            elif rec.stage_id.positions == 'create_user':
                if self.env.user == rec.user_id or self.user_has_groups('ejad_erp_helpdesk.group_helpdesk_create_user'):
                    rec.is_show_button = True

    @api.model_create_multi
    def create(self, list_value):
        res = super().create(list_value)
        res.update_user_id()
        res.create_activity()
        return res


class HelpdeskTeam(models.Model):
    _inherit = "helpdesk.team"

    assign_method = fields.Selection(selection_add=[('auto', 'تلقائي')],ondelete={'auto': 'cascade'})

    @api.constrains('assign_method', 'member_ids')
    def _check_member_assignation(self):
        if not self.member_ids and self.assign_method not in ('manual','auto'):
            raise ValidationError(_("You must have team members assigned to change the assignation method."))
