# -*- coding: utf-8 -*-

import logging
import time
from odoo import api, fields, models, _
from odoo.tools import float_compare
from odoo.exceptions import UserError, AccessError, ValidationError
from lxml import etree
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta

_logger = logging.getLogger(__name__)

from odoo.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


def convert_date_to_dayinweek(date):
    formatted_date = datetime.strptime(str(date), DEFAULT_SERVER_DATETIME_FORMAT)
    day_in_week = formatted_date.strftime("%A")
    return day_in_week


# class HrEmployee(models.Model):
#     _inherit = 'hr.employee'
#
#     contract_type = fields.Selection([('sicetific', 'هيئة علمية '),
#                                       ('management', 'ادارين'),
#                                       ('staff', 'مهنين')], string="نوع العقد")


class HREmployee(models.Model):
    _name = "hr.employee"
    _inherit = "hr.employee"

    def _compute_leave_status(self):
        # Used SUPERUSER_ID to forcefully get status of other user's leave, to bypass record rule
        holidays = self.env['hr.leave'].sudo().search([
            ('employee_id', 'in', self.ids),
            ('date_from', '<=', fields.Datetime.now()),
            ('date_to', '>=', fields.Datetime.now()),
            ('state', 'not in', ('cancel', 'refuse'))
        ])
        leave_data = {}
        for holiday in holidays:
            leave_data[holiday.employee_id.id] = {}
            leave_data[holiday.employee_id.id]['leave_date_from'] = holiday.date_from.date()
            leave_data[holiday.employee_id.id]['leave_date_to'] = holiday.date_to.date()
            leave_data[holiday.employee_id.id]['current_leave_state'] = holiday.state
            leave_data[holiday.employee_id.id]['current_leave_id'] = holiday.holiday_status_id.id

        for employee in self:
            employee.leave_date_from = leave_data.get(employee.id, {}).get('leave_date_from')
            employee.leave_date_to = leave_data.get(employee.id, {}).get('leave_date_to')
            employee.current_leave_state = leave_data.get(employee.id, {}).get('current_leave_state')
            employee.current_leave_id = leave_data.get(employee.id, {}).get('current_leave_id')
            employee.is_absent = leave_data.get(employee.id) and leave_data.get(employee.id, {}).get(
                'current_leave_state') not in ['cancel', 'refuse', 'draft']

    current_leave_state = fields.Selection(compute='_compute_leave_status', string="Current Leave Status",
                                           selection_add=[
                                               ('draft', 'To Submit'),
                                               ('cancel', 'Cancelled'),
                                               ('confirm', 'تم تقديم الطلب'),
                                               ('medical_manager', 'تمت موافقة المدير الطبي للجامعة'),
                                               ('direct_manager_approve', 'تمت موافقة المدير المباشر'),
                                               ('dept_manager_approve', 'تمت موافقة مدير /معتمد الإدارة'),
                                               ('academic_manager_approve', 'تمت موافقة  الوكيل للشؤون الأكادمية'),
                                               ('hr_checker', 'تمت موافقة مدقق الموارد البشرية'),
                                               ('validate1', 'Second Approval'),
                                               ('validate', 'مدير إدارة الموارد البشرية'),
                                               ('refuse', 'تم الرفض'),
                                           ])


class HRHolidaysStatus(models.Model):
    _name = "hr.leave.type"
    _inherit = "hr.leave.type"

    contract_type = fields.Selection([('sicetific', 'هيئة علمية '),
                                      ('management', 'ادارين'),
                                      ('staff', 'مهنين')], string="نوع العقد")

    is_annual_holiday = fields.Boolean('هل هي إجازة سنوية')
    is_permission = fields.Boolean('هل هي إستئذان')
    is_sick_holiday = fields.Boolean('هل هي إجازة مرضية')
    number_of_days_scientific = fields.Float('الهيئه العلمية')
    number_of_days_management = fields.Float('الإداريين')
    number_of_days_staff = fields.Float('المهنيين')
    number_of_days_per_year = fields.Float('عدد الأيام المسموح بها خلال السنة')
    number_of_days_old_date_request = fields.Float('عدد الأيام المسموح بها لطلب إجازة قبل التاريخ الحالي', default=2)

    def get_days(self, employee_id):
        # need to use `dict` constructor to create a dict per id
        self =self.sudo()
        result = dict((id, dict(max_leaves=0, leaves_taken=0, remaining_leaves=0, virtual_remaining_leaves=0)) for id in self.ids)
        requests = self.env['hr.leave'].search([
            ('employee_id', '=', employee_id),
            ('state', 'in', ['direct_manager','hr_approve','confirm', 'validate1', 'validate']),
            ('holiday_status_id', 'in', self.ids)
        ])

        allocations = self.env['hr.leave.allocation'].search([
            ('employee_id', '=', employee_id),
            ('state', 'in', ['confirm', 'validate1', 'validate']),
            ('holiday_status_id', 'in', self.ids)
        ])

        for request in requests:
            status_dict = result[request.holiday_status_id.id]
            status_dict['virtual_remaining_leaves'] -= (request.number_of_hours_display
                                                    if request.leave_type_request_unit == 'hour'
                                                    else request.number_of_days)
            if request.state == 'validate':
                status_dict['leaves_taken'] += (request.number_of_hours_display
                                            if request.leave_type_request_unit == 'hour'
                                            else request.number_of_days)
                status_dict['remaining_leaves'] -= (request.number_of_hours_display
                                                if request.leave_type_request_unit == 'hour'
                                                else request.number_of_days)

        for allocation in allocations.sudo():
            status_dict = result[allocation.holiday_status_id.id]
            if allocation.state == 'validate':
                # note: add only validated allocation even for the virtual
                # count; otherwise pending then refused allocation allow
                # the employee to create more leaves than possible
                status_dict['virtual_remaining_leaves'] += (allocation.number_of_hours_display
                                                          if allocation.type_request_unit == 'hour'
                                                          else allocation.number_of_days)
                status_dict['max_leaves'] += (allocation.number_of_hours_display
                                            if allocation.type_request_unit == 'hour'
                                            else allocation.number_of_days)
                status_dict['remaining_leaves'] += (allocation.number_of_hours_display
                                                  if allocation.type_request_unit == 'hour'
                                                  else allocation.number_of_days)

        return result

    # overwrite the original function get_days to just exclude cancel and refuse state
    def get_days_include_draft(self, employee_id):
        # need to use `dict` constructor to create a dict per id
        result = dict(
            (id, dict(max_leaves=0, leaves_taken=0, remaining_leaves=0, virtual_remaining_leaves=0)) for id in
            self.ids)

        requests = self.env['hr.leave'].search([
            ('employee_id', '=', employee_id),
            ('state', 'not in', ['cancel', 'refuse']),
            ('holiday_status_id', 'in', self.ids)
        ])

        allocations = self.env['hr.leave.allocation'].search([
            ('employee_id', '=', employee_id),
            ('state', 'not in', ['cancel', 'refuse']),
            ('holiday_status_id', 'in', self.ids)
        ])

        for request in requests:
            status_dict = result[request.holiday_status_id.id]
            status_dict['virtual_remaining_leaves'] -= (request.number_of_hours_display
                                                        if request.leave_type_request_unit == 'hour'
                                                        else request.number_of_days)
            if request.state == 'validate':
                status_dict['leaves_taken'] += (request.number_of_hours_display
                                                if request.leave_type_request_unit == 'hour'
                                                else request.number_of_days)
                status_dict['remaining_leaves'] -= (request.number_of_hours_display
                                                    if request.leave_type_request_unit == 'hour'
                                                    else request.number_of_days)

        for allocation in allocations.sudo():
            status_dict = result[allocation.holiday_status_id.id]
            if allocation.state == 'validate':
                # note: add only validated allocation even for the virtual
                # count; otherwise pending then refused allocation allow
                # the employee to create more leaves than possible
                status_dict['virtual_remaining_leaves'] += (allocation.number_of_hours_display
                                                            if allocation.type_request_unit == 'hour'
                                                            else allocation.number_of_days)
                status_dict['max_leaves'] += (allocation.number_of_hours_display
                                              if allocation.type_request_unit == 'hour'
                                              else allocation.number_of_days)
                status_dict['remaining_leaves'] += (allocation.number_of_hours_display
                                                    if allocation.type_request_unit == 'hour'
                                                    else allocation.number_of_days)

        return result


class HRHolidays(models.Model):
    _name = 'hr.leave'
    _inherit = 'hr.leave'

    message = fields.Char(compute="compute_message")
    substitute_employee = fields.Many2one('hr.employee', string="الموظف البديل")
    holiday_status_id = fields.Many2one(
        "hr.leave.type", string="نوع الأجازة", required=True, readonly=True,
        states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]},
        domain=[('valid', '=', True)])
    refuse_message = fields.Text("Refuse message", tracking=True)
    leave_validation_type = fields.Selection(string='Validation Type', related='holiday_status_id.leave_validation_type', readonly=False)

    def write(self, values):
        if not self.env.user.has_group('ejad_erp_hr.hr_holiday_create_old_date_request'):
            format = '%Y-%m-%d'
            effective_date = datetime.strptime(str(fields.Date.today()), format) + \
                             relativedelta(days=-self.holiday_status_id.number_of_days_old_date_request)
            if self.date_from and effective_date.date():
                if self.date_from.date() < effective_date.date():
                    raise ValidationError(
                        _('لقد تم تجاوز عدد الأيام المسموح بها لطلب إجازة بتاريخ قبل التاريخ الحالي'))

        employee_id = values.get('employee_id', False)
        if not self.env.context.get('leave_fast_create'):
            if values.get('state'):
                self._check_approval_update(values['state'])
                if any(holiday.leave_validation_type == 'both' for holiday in self):
                    if values.get('employee_id'):
                        employees = self.env['hr.employee'].browse(values.get('employee_id'))
                    else:
                        employees = self.mapped('employee_id')
                    self._check_double_validation_rules(employees, values['state'])
            if 'date_from' in values:
                values['request_date_from'] = values['date_from']
            if 'date_to' in values:
                values['request_date_to'] = values['date_to']
        result = super(models.Model, self).write(values)
        if not self.env.context.get('leave_fast_create'):
            for holiday in self:
                if employee_id:
                    holiday.add_follower(employee_id)
                    self._sync_employee_details()
                if 'number_of_days' not in values and ('date_from' in values or 'date_to' in values):
                    holiday._onchange_leave_dates()
        return result

    def unlink(self):
        error_message = _('You cannot delete a time off which is in %s state')
        state_description_values = {elem[0]: elem[1] for elem in self._fields['state']._description_selection(self.env)}

        if not self.user_has_groups('hr_holidays.group_hr_holidays_user'):
            if any(hol.state != 'draft' for hol in self):
                raise UserError(error_message % state_description_values.get(self[:1].state))
        else:
            for holiday in self.filtered(lambda holiday: holiday.state not in ['draft', 'cancel', 'confirm','refuse']):
                raise UserError(error_message % (state_description_values.get(holiday.state),))
        return super(models.Model, self).unlink()

    def get_date_to_dayinweek(self,date):
        if date:
            formatted_date = datetime.strptime(str(date), '%Y-%m-%d').date()
            day_in_week = formatted_date.strftime("%A") or ''

            week_list = {'Sunday' : 'الأحد' ,'Monday': 'الإثنين' ,'Tuesday' : 'الثلاثاء' ,'Wednesday' : 'الأربعاء' ,'Thursday' : 'الخميس' ,'Friday' : 'الجمعة' ,'Saturday' : 'السبت'}

            res = ''
            if (day_in_week in x for x in (week_list)):
                res = week_list[day_in_week]
        else:
            res = ''
        return res

    def compute_message(self):
        self.message = 'يتم الخصم من رصيد الأجازات بعد اعتماد الأجازة'

    def activity_update(self):
        to_clean, to_do = self.env['hr.leave'], self.env['hr.leave']
        for holiday in self:
            note = _('تم انشاء طلب %s بواسطة %s من %s الي %s') % (holiday.holiday_status_id.name, holiday.create_uid.name, fields.Datetime.to_string(holiday.date_from), fields.Datetime.to_string(holiday.date_to))
            if holiday.state == 'draft':
                to_clean |= holiday
            elif holiday.state == 'confirm':
                holiday.activity_schedule(
                    'hr_holidays.mail_act_leave_approval',
                    note=note,
                    user_id=holiday.sudo()._get_responsible_for_approval().id or self.env.user.id)
            elif holiday.state == 'validate1':
                holiday.activity_feedback(['hr_holidays.mail_act_leave_approval'])
                holiday.activity_schedule(
                    'hr_holidays.mail_act_leave_second_approval',
                    note=note,
                    user_id=holiday.sudo()._get_responsible_for_approval().id or self.env.user.id)
            elif holiday.state == 'validate':
                to_do |= holiday
            elif holiday.state == 'refuse':
                to_clean |= holiday
        if to_clean:
            to_clean.activity_unlink(['hr_holidays.mail_act_leave_approval', 'hr_holidays.mail_act_leave_second_approval'])
        if to_do:
            to_do.activity_feedback(['hr_holidays.mail_act_leave_approval', 'hr_holidays.mail_act_leave_second_approval'])

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        # print('##################   $$$')
        if self.env.user.has_group('ejad_erp_hr.group_medical_manager'):
            if self.env.user.has_group('ejad_erp_hr.access_all_employee') or self.env.user.has_group(
                    'ejad_erp_hr.access_all_hr_leaves'):
                domain += [('id', '!=', -1)]
            elif self.env.user.has_group('ejad_erp_hr.access_department_employee_only'):
                domain += ['|', '|', ('holiday_status_id.is_sick_holiday', '=', True),
                           ('employee_id.parent_id.user_id', '=', self.env.user.id),
                           ('employee_id.department_id', 'child_of',
                            self.env.user.employee_ids and
                            self.env.user.employee_ids[
                                0].department_id.id or [])]
            elif self.env.user.has_group('ejad_erp_hr.access_direct_employee_manager_only'):
                domain += ['|', '|', ('holiday_status_id.is_sick_holiday', '=', True),
                           ('employee_id.parent_id.user_id', '=', self.env.user.id),
                           ('employee_id.user_id', '=', self.env.user.id)]
            elif self.env.user.has_group('ejad_erp_hr.access_general_employee_only'):
                domain += ['|', ('holiday_status_id.is_sick_holiday', '=', True),
                           ('employee_id.user_id', '=', self.env.user.id)]
            else:
                domain += ['|', ('holiday_status_id.is_sick_holiday', '=', True), ('id', '=', -1)]
        else:
            if self.env.user.has_group('ejad_erp_hr.access_all_employee') or self.env.user.has_group(
                    'ejad_erp_hr.access_all_hr_leaves'):
                domain += [('id', '!=', -1)]
            elif self.env.user.has_group('ejad_erp_hr.access_department_employee_only'):
                domain += ['|', ('employee_id.parent_id.user_id', '=', self.env.user.id),
                           ('employee_id.department_id', 'child_of',
                            self.env.user.employee_ids and
                            self.env.user.employee_ids[
                                0].department_id.id or [])]
            elif self.env.user.has_group('ejad_erp_hr.access_direct_employee_manager_only'):
                domain += ['|', ('employee_id.parent_id.user_id', '=', self.env.user.id),
                           ('employee_id.user_id', '=', self.env.user.id)]
            elif self.env.user.has_group('ejad_erp_hr.access_general_employee_only'):
                domain += [('employee_id.user_id', '=', self.env.user.id)]
            else:
                domain += [('id', '=', -1)]
        res = super(HRHolidays, self).read_group(domain, fields, groupby, offset=offset, limit=limit,
                                                 orderby=orderby, lazy=lazy)
        return res

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(HRHolidays, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
                                                      submenu=submenu)
        doc = etree.XML(res['arch'])
        nodes = doc.xpath("//field[@name='employee_id']")
        for node in nodes:
            if self.env.user.has_group('ejad_erp_hr.access_all_employee'):
                node.set('domain', str([('id', '!=', -1)]))
            elif self.env.user.has_group('ejad_erp_hr.access_department_employee_only'):
                node.set('domain', str(['|', ('parent_id.user_id', '=', self.env.user.id), ('department_id', 'child_of',
                                                                                            self.env.user.employee_ids and
                                                                                            self.env.user.employee_ids[
                                                                                                0].department_id.id or [])]))
            elif self.env.user.has_group('ejad_erp_hr.access_direct_employee_manager_only'):
                node.set('domain',
                         str(['|', ('parent_id.user_id', '=', self.env.user.id), ('user_id', '=', self.env.user.id)]))
            elif self.env.user.has_group('ejad_erp_hr.access_general_employee_only'):
                node.set('domain', str([('user_id', '=', self.env.user.id)]))
            else:
                node.set('domain', str([('id', '=', -1)]))
        nodes2 = doc.xpath("//field[@name='replaced_employee_id']")
        for node in nodes2:

            if self.env.user.has_group('ejad_erp_hr.access_all_employee'):
                node.set('domain', str([('id', '!=', -1)]))
            else:
                node.set('domain', str(['|', '|', ('parent_id.user_id', '=', self.env.user.id), ('department_id', '=',
                                                                                                 self.env.user.employee_ids and
                                                                                                 self.env.user.employee_ids[
                                                                                                     0].department_id.id or []),
                                        ('id', '=', self.env.user.employee_ids and self.env.user.employee_ids[
                                            0].parent_id.id or [])]))
            # elif self.env.user.has_group('ejad_erp_hr.access_direct_employee_manager_only'):
            #    node.set('domain',
            #             str(['|', ('parent_id.user_id', '=', self.env.user.id), ('user_id', '=', self.env.user.id)]))
            # elif self.env.user.has_group('ejad_erp_hr.access_general_employee_only'):
            #    node.set('domain', str([('user_id', '=', self.env.user.id)]))
            # else:
            #    node.set('domain', str([('id', '=', -1)]))
        res['arch'] = etree.tostring(doc)
        return res

    @api.model
    def search(self, domain, offset=0, limit=None, order=None, count=False):
        if self.env.user.has_group('ejad_erp_hr.group_medical_manager'):
            if self.env.user.has_group('ejad_erp_hr.access_all_employee') or self.env.user.has_group(
                    'ejad_erp_hr.access_all_hr_leaves'):
                domain += [('id', '!=', -1)]
            elif self.env.user.has_group('ejad_erp_hr.access_department_employee_only'):
                domain += ['|', '|', ('holiday_status_id.is_sick_holiday', '=', True),
                           ('employee_id.parent_id.user_id', '=', self.env.user.id),
                           ('employee_id.department_id', 'child_of',
                            self.env.user.employee_ids and
                            self.env.user.employee_ids[
                                0].department_id.id or [])]
            elif self.env.user.has_group('ejad_erp_hr.access_direct_employee_manager_only'):
                domain += ['|', '|', ('holiday_status_id.is_sick_holiday', '=', True),
                           ('employee_id.parent_id.user_id', '=', self.env.user.id),
                           ('employee_id.user_id', '=', self.env.user.id)]
            elif self.env.user.has_group('ejad_erp_hr.access_general_employee_only'):
                domain += ['|', ('holiday_status_id.is_sick_holiday', '=', True),
                           ('employee_id.user_id', '=', self.env.user.id)]
            else:
                domain += ['|', ('holiday_status_id.is_sick_holiday', '=', True), ('id', '=', -1)]
        else:
            if self.env.user.has_group('ejad_erp_hr.access_all_employee') or self.env.user.has_group(
                    'ejad_erp_hr.access_all_hr_leaves'):
                domain += [('id', '!=', -1)]
            elif self.env.user.has_group('ejad_erp_hr.access_department_employee_only'):
                domain += ['|', ('employee_id.parent_id.user_id', '=', self.env.user.id),
                           ('employee_id.department_id', 'child_of',
                            self.env.user.employee_ids and
                            self.env.user.employee_ids[
                                0].department_id.id or [])]
            elif self.env.user.has_group('ejad_erp_hr.access_direct_employee_manager_only'):
                domain += ['|', ('employee_id.parent_id.user_id', '=', self.env.user.id),
                           ('employee_id.user_id', '=', self.env.user.id)]
            elif self.env.user.has_group('ejad_erp_hr.access_general_employee_only'):
                domain += [('employee_id.user_id', '=', self.env.user.id)]
            elif self.env.user.has_group('ejad_erp_hr.hr_holidays_access_direct_manger'):
                domain += ['|', ('employee_id.parent_id.user_id', '=', self.env.user.id),
                           ('employee_id.user_id', '=', self.env.user.id)]
            else:
                domain += [('id', '=', -1)]
        res = super(HRHolidays, self).search(domain, offset=offset, limit=limit, order=order,
                                             count=count)
        return res

    def action_refuse(self):
        current_employee = self.env.user.employee_id
        if any(holiday.state not in ['draft', 'confirm', 'validate', 'validate1'] for holiday in self):
            raise UserError(_('Time off request must be confirmed or validated in order to refuse it.'))

        validated_holidays = self.filtered(lambda hol: hol.state == 'validate1')
        validated_holidays.write({'state': 'refuse', 'first_approver_id': current_employee.id})
        (self - validated_holidays).write({'state': 'refuse', 'second_approver_id': current_employee.id})
        # Delete the meeting
        self.mapped('meeting_id').unlink()
        # If a category that created several holidays, cancel all related
        linked_requests = self.mapped('linked_request_ids')
        if linked_requests:
            linked_requests.action_refuse()

        # Post a second message, more verbose than the tracking message
        for holiday in self:
            if holiday.employee_id.user_id:
                holiday.message_post(
                    body=_('Your %s planned on %s has been refused') % (
                        holiday.holiday_status_id.display_name, holiday.date_from),
                    partner_ids=holiday.employee_id.user_id.partner_id.ids)
                # update dynamic workflow stage_id
                # stage_id = holiday.stage_ids.filtered(lambda r: r.holidays_state in (holiday.state))

                # holiday.write({'stage_id': stage_id.id})

        self._remove_resource_leave()
        self.activity_update()
        return True

    def action_draft(self):
        if any(holiday.state not in ['confirm', 'refuse'] for holiday in self):
            raise UserError(
                _('Time off request state must be "Refused" or "To Approve" in order to be reset to draft.'))
        self.write({
            'state': 'draft',
            'first_approver_id': False,
            'second_approver_id': False,
        })

        # select draft dynamic workflow
        # stage_id = self.stage_ids.filtered(lambda r: r.stage_type == 'is_first')
        self.write({
            # 'stage_id': stage_id.id,
            'state': 'draft',
            'first_approver_id': False,
            'second_approver_id': False,
        })

        linked_requests = self.mapped('linked_request_ids')
        if linked_requests:
            linked_requests.action_draft()
            linked_requests.unlink()
        self.activity_update()
        return True

    # @api.onchange('date_to', 'date_from')
    # def _onchange_date_to(self):
    #     """ Update the number_of_days. """
    #     date_from = self.date_from
    #     date_to = self.date_to
    #     if (date_to and date_from) and (date_from <= date_to):
    #         from_dt = fields.Datetime.from_string(date_from)
    #         to_dt = fields.Datetime.from_string(date_to)
    #
    #         self.number_of_days = (to_dt.date() - from_dt.date()).days + 1
    #     else:
    #         self.number_of_days = 0
    #
    #     # math.ceil(time_delta.days + float(time_delta.seconds) / 86400)

    state = fields.Selection(selection_add=[
        ('draft', 'الموظف'),
        ('cancel', 'Cancelled'),
        ('direct_manager', 'المدير المباشر'),
        ('hr_approve', 'مسؤول الموارد البشرية'),
        ('confirm', 'مدير إدارة الخدمات المساندة'),
        ('validate1', 'قائد المكتب'),
        ('validate', 'تم الموافقة'),
        ('refuse', 'تم الرفض'),

    ], string='Status', readonly=True, tracking=True, copy=False, default='draft',
        help="The status is set to 'To Submit', when a leave request is created." +
             "\nThe status is 'To Approve', when leave request is confirmed by user." +
             "\nThe status is 'Refused', when leave request is refused by manager." +
             "\nThe status is 'Approved', when leave request is approved by manager.",translate=False)

    state1 = fields.Selection([
        ('draft', 'الموظف'),
        ('cancel', 'Cancelled'),
        ('direct_manager', 'المدير المباشر'),
        ('hr_approve', 'مسؤول الموارد البشرية'),
        ('confirm', 'مدير إدارة الخدمات المساندة'),
        ('validate1', 'قائد المكتب'),
        ('validate', 'تم الموافقة'),
        ('refuse', 'تم الرفض'),

    ], string='Status', readonly=True, tracking=True, copy=False, default='draft',
        help="The status is set to 'To Submit', when a leave request is created." +
             "\nThe status is 'To Approve', when leave request is confirmed by user." +
             "\nThe status is 'Refused', when leave request is refused by manager." +
             "\nThe status is 'Approved', when leave request is approved by manager.", translate=False)

    replaced_employee_id = fields.Many2one('hr.employee', string='Replaced Employee', tracking=True)
    # employee_id = fields.Many2one('hr.employee')
    medical_manger_button = fields.Boolean('show button', compute='_show_buttons')
    direct_manger_button = fields.Boolean('show button', compute='_show_buttons_direct_manager')
    academic_manger_button = fields.Boolean('show button', compute='_show_buttons')
    hr_checker_button = fields.Boolean('show button', compute='_show_buttons')
    hr_manager_button = fields.Boolean('show button', compute='_show_buttons')
    hr_dept_manger_button = fields.Boolean('show button', compute='_show_buttons')
    dynamic_workflow_button = fields.Boolean('show dynamic workflow button', compute='_show_buttons')
    tickets_number = fields.Integer('Tickets Number')
    salary_advance = fields.Boolean('Advance Salary')
    is_annual_holiday = fields.Boolean(related='holiday_status_id.is_annual_holiday')
    is_permission = fields.Boolean(related='holiday_status_id.is_permission')
    is_scientific = fields.Boolean(compute='_compute_is_scientific', store=True)
    # manager_menagment_id = fields.Many2one('hr.employee', string='المدير المعتمد', compute='_add_manager_managment')
    permission_type_id = fields.Many2one('hr.permissions', string='نوع الإستئذان')
    manager_menagment_id = fields.Many2one('hr.employee', string='المدير المعتمد', compute='_add_manager_managment',
                                           store=True)

    date_from = fields.Datetime(readonly=True,
                                states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]})
    date_to = fields.Datetime(readonly=True, states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]})
    leave_return_id = fields.Many2one('hr.leave.return', string='Leave Return',readonly=True)

    @api.model
    def default_get(self, fields_list):
        defaults = super(HRHolidays, self).default_get(fields_list)
        defaults = self._default_get_request_parameters(defaults)

        LeaveType = self.env['hr.leave.type'].with_context(employee_id=defaults.get('employee_id'), default_date_from=defaults.get('date_from', fields.Datetime.now()))
        lt = LeaveType.search([('valid', '=', True)], limit=1)

        defaults['holiday_status_id'] = lt.id if lt else defaults.get('holiday_status_id')
        defaults['state'] = 'draft'
        return defaults

    @api.onchange('holiday_status_id')
    def _onchange_holiday_status_id(self):
        self.request_unit_half = False
        self.request_unit_hours = False
        self.request_unit_custom = False
        self.state = 'draft'

    def action_confirm(self):
        for rec in self:
            if self.filtered(lambda holiday: holiday.state != 'direct_manager'):
                raise UserError(_('Time off request must be in direct_manager  state ("To Submit") in order to confirm it.'))
            self.write({'state': 'hr_approve'})
            self.write({'state1': 'hr_approve'})
            holidays = self.filtered(lambda leave: leave.leave_validation_type == 'no_validation')
            if holidays:
                # Automatic validation should be done in sudo, because user might not have the rights to do it by himself
                holidays.sudo().action_validate()
            self.activity_update()
            for user in rec.get_users('ejad_erp_hr.group_hr_holiday_specialist'):
                rec.activity_feedback(['mail.mail_activity_data_todo'],
                                      feedback='تم اكمال المهمة بنجاح شكرا لك')
                rec.activity_schedule('mail.mail_activity_data_todo',
                                      user_id=user,
                                      res_id=rec.id)
        return True

    def get_last_holidays(self,employee_id):
        for rec in self:
            holidays = self.env['hr.leave'].search([
                ('employee_id', '=', employee_id),
                ('id', '!=', rec.id),
                ('state', 'in', ['confirm', 'validate1', 'validate']),
                ('holiday_status_id', '=', rec.holiday_status_id.id)
            ],limit=1,order="id desc")
            if holidays and holidays.create_date:
                return holidays.create_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
            else:
                return False

    def get_employee_spcail(self,num):
        for rec in self:
            user_list = []
            users = self.env['res.users']
            user_list_group = rec.get_users('ejad_erp_hr.group_support_services_manager')
            vals = [1,2,3,4,5]
            user_last = filter(lambda x : x not in vals,user_list_group)
            user_list.append(users.browse(u for u in user_last))
            if len(user_list) > 0:
                if num == 1:
                    result = ','.join(i.name for i in user_list)
                if num == 2:
                    for rec in user_list:
                       result = rec
                return result
            else:
                return False

    def action_direct_manager(self):
        for rec in self:
            if rec.employee_id.sudo().parent_id.user_id:
                rec.activity_feedback(['mail.mail_activity_data_todo'],
                                      feedback='تم اكمال المهمة بنجاح شكرا لك')
                rec.activity_schedule('mail.mail_activity_data_todo',
                                      user_id=rec.employee_id.sudo().parent_id.user_id.id,
                                      res_id=rec.id)
            rec.write({'state': 'direct_manager'})
            rec.write({'state1': 'direct_manager'})

    def action_support_service(self):
        for rec in self:
            for user in rec.get_users('ejad_erp_hr.group_support_services_manager'):
                rec.activity_feedback(['mail.mail_activity_data_todo'],
                                      feedback='تم اكمال المهمة بنجاح شكرا لك')
                rec.activity_schedule('mail.mail_activity_data_todo',
                                      user_id=user,
                                      res_id=rec.id)

            rec.write({'state': 'confirm'})
            rec.write({'state1': 'confirm'})

    def get_users(self, group_name):
        user_ids = []
        users = self.env['res.users'].search([])
        for user in users:
            if user.has_group(group_name):
                user_ids.append(user.id)
        if len(user_ids) > 0:
            return user_ids
        else:
            raise ValidationError(('لم يتم تخصيص الشخص المعني للمرحلة القادمة'))

    def _add_manager_managment(self):
        for record in self:
            if record.department_id.type == 'dept':
                record.manager_menagment_id = record.sudo().department_id.parent_id.manager_id.id
            else:
                record.manager_menagment_id = False

    @api.depends('employee_id', 'employee_id.contract_type')
    def _compute_is_scientific(self):
        for record in self:
            if record.employee_id.contract_type == 'sicetific':
                record.is_scientific = True
            else:
                record.is_scientific = False

    def _show_buttons_direct_manager(self):
        if self.env.user == self.sudo().employee_id.parent_id.user_id \
                or self.user_has_groups('ejad_erp_hr.hr_holidays_direct_manager') \
                or (self.employee_id.user_id and self.env.uid == self.employee_id.user_id.id
                    and self.user_has_groups('ejad_erp_hr.hr_holiday_employee_itself_direct_manager')):
            self.direct_manger_button = True

        else:
            self.direct_manger_button = False

    @api.depends('state', 'holiday_status_id','holiday_status_id.is_sick_holiday')
    def _show_buttons(self):

        self.dynamic_workflow_button = False
        if self.holiday_status_id.is_sick_holiday and self.state == 'confirm':
            self.medical_manger_button = True
            self.dynamic_workflow_button = True
        else:
            self.medical_manger_button = False

        if self.employee_id.department_id.type == 'dept' and self.state == 'direct_manager_approve':

            dept_manager = self.sudo().employee_id.department_id.parent_id.manager_id.user_id
            if self.env.user == dept_manager or self.user_has_groups('ejad_erp_hr.hr_holidays_dept_manger'):
                self.hr_dept_manger_button = True
                self.dynamic_workflow_button = True
            else:
                self.hr_dept_manger_button = False

        else:
            self.hr_dept_manger_button = False

        if self.employee_id.contract_type == 'sicetific' and self.state == 'dept_manager_approve' or (
                self.employee_id.contract_type == 'sicetific' and
                not self.employee_id.department_id.type == 'dept' and self.state == 'direct_manager_approve'):
            self.academic_manger_button = True
            self.dynamic_workflow_button = True
        else:
            self.academic_manger_button = False

        if self.state == 'academic_manager_approve' or (
                not self.employee_id.contract_type == 'sicetific' and not self.employee_id.department_id.type == 'dept'
                and self.state == 'direct_manager_approve') or (not self.employee_id.contract_type == 'sicetific'
                                                                and self.state == 'dept_manager_approve'):
            self.hr_checker_button = True
            self.dynamic_workflow_button = True
        else:
            self.hr_checker_button = False
        if self.state == 'hr_checker':
            self.hr_manager_button = True
            self.dynamic_workflow_button = True
        else:
            self.hr_manager_button = False

    def _check_double_validation_rules(self, employees, state):
        return

    def action_refuse(self):
        current_employee = self.env.user.employee_id
        if any(holiday.state not in ['draft','direct_manager', 'confirm', 'validate', 'validate1','hr_approve'] for holiday in self):
            raise UserError(_('Time off request must be confirmed or validated in order to refuse it.'))

        validated_holidays = self.filtered(lambda hol: hol.state == 'validate1')
        validated_holidays.write({'state': 'refuse', 'first_approver_id': current_employee.id})
        (self - validated_holidays).write({'state': 'refuse', 'second_approver_id': current_employee.id})
        # Delete the meeting
        self.mapped('meeting_id').unlink()
        # If a category that created several holidays, cancel all related
        linked_requests = self.mapped('linked_request_ids')
        if linked_requests:
            linked_requests.action_refuse()

        # Post a second message, more verbose than the tracking message
        for holiday in self:
            if holiday.employee_id.user_id:
                holiday.message_post(
                    body=_('Your %s planned on %s has been refused') % (holiday.holiday_status_id.display_name, holiday.date_from),
                    partner_ids=holiday.employee_id.user_id.partner_id.ids)

        self._remove_resource_leave()
        self.activity_feedback(['mail.mail_activity_data_todo'],
                               feedback='تم اكمال المهمة بنجاح شكرا لك')
        self.activity_update()
        return True

    def action_approve(self):
        # if leave_validation_type == 'both': this method is the first approval approval
        # if leave_validation_type != 'both': this method calls action_validate() below
        if any(holiday.state != 'confirm' for holiday in self):
            raise UserError(_('Time off request must be confirmed ("To Approve") in order to approve it.'))

        current_employee = self.env.user.employee_id
        self.filtered(lambda hol: hol.leave_validation_type == 'both').write({'state': 'validate1', 'first_approver_id': current_employee.id})


        # Post a second message, more verbose than the tracking message
        for holiday in self.filtered(lambda holiday: holiday.employee_id.user_id):
            holiday.message_post(
                body=_('Your %s planned on %s has been accepted' % (holiday.holiday_status_id.display_name, holiday.date_from)),
                partner_ids=holiday.employee_id.user_id.partner_id.ids)

        self.filtered(lambda hol: not hol.leave_validation_type == 'both').action_validate()
        if not self.env.context.get('leave_fast_create'):
            self.activity_update()
        for user in self.get_users('ejad_erp_hr.group_hr_holiday_office_leader'):
            self.activity_feedback(['mail.mail_activity_data_todo'],
                                  feedback='تم اكمال المهمة بنجاح شكرا لك')
            self.activity_schedule('mail.mail_activity_data_todo',
                                  user_id=user,
                                  res_id=self.id)

        return True

    def action_approve_hr_manger(self):
        # if double_validation: this method is the first approval approval
        # if not double_validation: this method calls action_validate() below
        # self._check_security_action_approve()

        current_employee = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        for holiday in self:
            # if holiday.state != 'confirm':
            #     raise UserError(_('Leave request must be confirmed ("To Approve") in order to approve it.'))
            # double_validation not found in odoo 13
            # if holiday.double_validation:
            #     return holiday.write({'state': 'validate1', 'first_approver_id': current_employee.id})
            # else:
            holiday.action_validate()

    # odoo 13
    # def _get_remaining_leaves_for_annual(self,employees):
    #     annual_holiday = self.env['hr.leave.type'].search([('is_annual_holiday', '=', True)], limit=1)
    #
    #
    #     self._cr.execute("""
    #         SELECT
    #             sum(h.number_of_days) AS days,
    #             h.employee_id
    #         FROM
    #             hr_holidays h
    #             join hr_holidays_status s ON (s.id=%s)
    #         WHERE
    #             h.state='validate' AND
    #             h.employee_id in %s AND
    #             h.type = 'remove'
    #
    #         GROUP BY h.employee_id""", (annual_holiday.id,tuple(employees.ids),))
    #     return dict((row['employee_id'], row['days']) for row in self._cr.dictfetchall())
    def _check_approval_update(self, state):
        """ Check if target state is achievable. """
        return

    @api.constrains('state1','state', 'date_from')
    def _check_holiday_request_old_dates(self):
        for record in self:
            if (record.state == 'confirm' or record.state1 == 'validate') \
                    and record.date_from.date() < fields.Date.today() \
                    and record.holiday_status_id.number_of_days_old_date_request \
                    and not self.env.user.has_group('ejad_erp_hr.hr_holiday_create_old_date_request'):
                format = '%Y-%m-%d'
                effective_date = datetime.strptime(str(fields.Date.today()), format) + \
                                 relativedelta(days=-record.holiday_status_id.number_of_days_old_date_request)

                if record.date_from.date() < effective_date.date():
                    raise ValidationError(
                        _('لقد تم تجاوز عدد الأيام المسموح بها لطلب إجازة بتاريخ قبل التاريخ الحالي'))

    @api.constrains('state', 'date_from', 'date_to')
    def _check_holiday_number_of_days_per_year(self):
        for record in self:
            if record.state == 'confirm' and record.holiday_status_id.number_of_days_per_year \
                    and not self.env.user.has_group('ejad_erp_hr.hr_holiday_exceed_number_of_days_per_year'):
                holidays_during_year_per_type = self.env['hr.leave'].search([
                    ('holiday_status_id', '=', self.holiday_status_id.id),
                    ('employee_id', '=', self.employee_id.id),
                    ('date_to', '>=', time.strftime('%Y-01-01')),
                    ('date_from', '<=', time.strftime('%Y-12-31'))])

                d_start_str = time.strftime('%Y-01-01')
                d_end_str = time.strftime('%Y-12-31')
                d_start = datetime.strptime(d_start_str, "%Y-%m-%d").date()
                d_end = datetime.strptime(d_end_str, "%Y-%m-%d").date()
                no_days_per_year = 0
                for holiday in holidays_during_year_per_type:
                    date_from = str(holiday.date_from)
                    date_to = str(holiday.date_to)
                    d_from = datetime.strptime(date_from, "%Y-%m-%d").date()
                    d_to = datetime.strptime(date_to, "%Y-%m-%d").date()
                    if holiday.date_from <= d_start_str and holiday.date_to <= d_end_str:
                        no_days_per_year += abs((d_to - d_start).days) + 1

                    elif holiday.date_from >= d_start_str and holiday.date_to <= d_end_str:
                        no_days_per_year += abs((d_to - d_from).days) + 1

                    elif holiday.date_from >= d_start_str and holiday.date_to >= d_end_str:
                        no_days_per_year += abs((d_end - d_from).days) + 1

                    elif holiday.date_from <= d_start_str and holiday.date_to >= d_end_str:
                        no_days_per_year += abs((d_end - d_start).days) + 1

                    else:
                        pass
                    if no_days_per_year > record.holiday_status_id.number_of_days_per_year:
                        raise ValidationError(
                            _('لقد تم تجاوز عدد الأيام المسموح بها لهذا النوع من الإجازة خلال السنة الميلادية'))

    # @api.constrains('state', 'number_of_days', 'holiday_status_id')
    # def _check_holidays(self):
    #     for holiday in self:
    #         if holiday.holiday_type != 'employee' or not holiday.employee_id or holiday.holiday_status_id.allocation_type == 'no':
    #             continue
    #         leave_days = holiday.holiday_status_id.get_days_include_draft(holiday.employee_id.id)[
    #             holiday.holiday_status_id.id]
    #         date_from = str(self.date_from.date())
    #         holiday_date_from = datetime.strptime(date_from, "%Y-%m-%d").date()
    #         today = str(fields.Date.today())
    #         today_date = datetime.strptime(today, "%Y-%m-%d").date()
    #         future_allocate_days = 0
    #         if holiday_date_from > today_date:
    #             no_days_until_holiday_start = abs(holiday_date_from - today_date).days
    #
    #             annual_holiday = self.env['hr.leave.type'].search([('is_annual_holiday', '=', True)], limit=1)
    #             if annual_holiday:
    #                 allocate_days = 0
    #             if self.employee_id.contract_type == 'sicetific':
    #                 allocate_days = annual_holiday.number_of_days_scientific / 360
    #             elif self.employee_id.contract_type == 'management':
    #                 allocate_days = annual_holiday.number_of_days_management / 360
    #
    #             elif self.employee_id.contract_type == 'staff':
    #                 allocate_days = annual_holiday.number_of_days_staff / 360
    #
    #             future_allocate_days = allocate_days * no_days_until_holiday_start
    #
    #         if float_compare(leave_days['remaining_leaves'] + future_allocate_days, 0, precision_digits=2) == -1 or \
    #                 float_compare(leave_days['virtual_remaining_leaves'] + future_allocate_days, 0,
    #                               precision_digits=2) == -1:
    #             raise ValidationError(_('The number of remaining leaves is not sufficient for this leave type.\n'
    #                                     'Please verify also the leaves waiting for validation.'))
    def _validate_leave_request(self):
        """ Validate time off requests (holiday_type='employee')
        by creating a calendar event and a resource time off. """
        holidays = self.filtered(lambda request: request.holiday_type == 'employee')
        holidays._create_resource_leave()
        for holiday in holidays.filtered(lambda l: l.holiday_status_id.create_calendar_meeting):
            meeting_values = holiday._prepare_holidays_meeting_values()
            meeting = self.env['calendar.event'].with_context(no_mail_to_attendees=True, active_model=self._name).create(meeting_values)
            holiday.write({'meeting_id': meeting.id})

    def action_validate(self):
        current_employee = self.env.user.employee_id
        # if any(holiday.state not in ['confirm', 'validate1'] for holiday in self):
        #     raise UserError(_('Time off request must be confirmed in order to approve it.'))

        self.write({'state': 'validate'})
        self.write({'state1': 'validate'})
        self.filtered(lambda holiday: holiday.leave_validation_type == 'both').write(
            {'second_approver_id': current_employee.id})
        self.filtered(lambda holiday: holiday.leave_validation_type != 'both').write(
            {'first_approver_id': current_employee.id})

        for holiday in self.filtered(lambda holiday: holiday.holiday_type != 'employee'):
            if holiday.holiday_type == 'category':
                employees = holiday.category_id.employee_ids
            elif holiday.holiday_type == 'company':
                employees = self.env['hr.employee'].search([('company_id', '=', holiday.mode_company_id.id)])
            else:
                employees = holiday.department_id.member_ids

            conflicting_leaves = self.env['hr.leave'].with_context(
                tracking_disable=True,
                mail_activity_automation_skip=True,
                leave_fast_create=True
            ).search([
                ('date_from', '<=', holiday.date_to),
                ('date_to', '>', holiday.date_from),
                ('state', 'not in', ['cancel', 'refuse']),
                ('holiday_type', '=', 'employee'),
                ('employee_id', 'in', employees.ids)])

            if conflicting_leaves:
                # YTI: More complex use cases could be managed in master
                if holiday.leave_type_request_unit != 'day' or any(
                        l.leave_type_request_unit == 'hour' for l in conflicting_leaves):
                    raise ValidationError(_('You can not have 2 leaves that overlaps on the same day.'))

                for conflicting_leave in conflicting_leaves:
                    if conflicting_leave.leave_type_request_unit == 'half_day' and conflicting_leave.request_unit_half:
                        conflicting_leave.action_refuse()
                        continue
                    # Leaves in days
                    split_leaves = self.env['hr.leave']
                    target_state = conflicting_leave.state
                    conflicting_leave.action_refuse()
                    if conflicting_leave.date_from < holiday.date_from:
                        before_leave_vals = conflicting_leave.copy_data({
                            'date_from': conflicting_leave.date_from.date(),
                            'date_to': holiday.date_from.date() + timedelta(days=-1),
                        })[0]
                        before_leave = self.env['hr.leave'].new(before_leave_vals)
                        before_leave._onchange_request_parameters()
                        # Could happen for part-time contract, that time off is not necessary
                        # anymore.
                        # Imagine you work on monday-wednesday-friday only.
                        # You take a time off on friday.
                        # We create a company time off on friday.
                        # By looking at the last attendance before the company time off
                        # start date to compute the date_to, you would have a date_from > date_to.
                        # Just don't create the leave at that time. That's the reason why we use
                        # new instead of create. As the leave is not actually created yet, the sql
                        # constraint didn't check date_from < date_to yet.
                        if before_leave.date_from < before_leave.date_to:
                            split_leaves |= self.env['hr.leave'].with_context(
                                tracking_disable=True,
                                mail_activity_automation_skip=True,
                                leave_fast_create=True
                            ).create(before_leave._convert_to_write(before_leave._cache))
                    if conflicting_leave.date_to > holiday.date_to:
                        after_leave_vals = conflicting_leave.copy_data({
                            'date_from': holiday.date_to.date() + timedelta(days=1),
                            'date_to': conflicting_leave.date_to.date(),
                        })[0]
                        after_leave = self.env['hr.leave'].new(after_leave_vals)
                        after_leave._onchange_request_parameters()
                        # Could happen for part-time contract, that time off is not necessary
                        # anymore.
                        if after_leave.date_from < after_leave.date_to:
                            split_leaves |= self.env['hr.leave'].with_context(
                                tracking_disable=True,
                                mail_activity_automation_skip=True,
                                leave_fast_create=True
                            ).create(after_leave._convert_to_write(after_leave._cache))
                    for split_leave in split_leaves:
                        if target_state == 'draft':
                            continue
                        if target_state == 'confirm':
                            split_leave.action_confirm()
                        elif target_state == 'validate1':
                            split_leave.action_confirm()
                            split_leave.action_approve()
                        elif target_state == 'validate':
                            split_leave.action_confirm()
                            split_leave.action_validate()

            values = [holiday._prepare_holiday_values(employee) for employee in employees]
            leaves = self.env['hr.leave'].with_context(
                tracking_disable=True,
                mail_activity_automation_skip=True,
                leave_fast_create=True,
            ).create(values)
            leaves.action_approve()
            # FIXME RLi: This does not make sense, only the parent should be in leave_validation_type both
            if leaves and leaves[0].leave_validation_type == 'both':
                leaves.action_validate()
        employee_requests = self.filtered(lambda hol: hol.holiday_type == 'employee')

        employee_requests._validate_leave_request()
        self.activity_feedback(['mail.mail_activity_data_todo'],
                               feedback='تم اكمال المهمة بنجاح شكرا لك')
        if not self.env.context.get('leave_fast_create'):
            employee_requests.filtered(lambda holiday: holiday.leave_validation_type != 'no_validation').activity_update()
        if self.replaced_employee_id:
            template = self.env.ref("ejad_erp_hr.hr_leave_notify_replaced_employee_mail_template")
            try:

                self.env['mail.template'].sudo().browse(template.id).send_mail(self.id)
                self.message_post(body=_("لقد تم إختيارك كموظف بديل للموظف %s") % (
                self.employee_id.name), message_type='email',
                                  subject='لقد تم إختيارك كموظف بديل')
            except:
                pass

        if self.employee_id:
            template_leave_approve = self.env.ref("ejad_erp_hr.hr_leave_approve_notify_employee_mail_template")

            try:

                self.env['mail.template'].sudo().browse(template_leave_approve.id).send_mail(self.id)
                self.message_post(body=_("لقد تم الموافقة على طلب الاجازة %s") % (
                self.employee_id.name), message_type='email',
                                  subject='لقد تم الموافقة على طلب الاجازة')
            except:
                pass
        return True

    """
        Start workflow fields ( حقول المراحل )
    """
    category = fields.Many2one("dynamic.workflow.category", string="Category", tracking=True)

    project_type = fields.Many2one('workflow.project.type', string="Project type", compute="get_project_type", store=False)
    # default=lambda self: self.env.ref('ejad_erp_hr.holidays_project_type_data').id,
    project_code = fields.Char(related="project_type.code")

    stage_ids = fields.Many2many("dynamic.workflow.stage", compute="_compute_stage_ids", tracking=True)
    stage_id = fields.Many2one("dynamic.workflow.stage", string="المرحلة", tracking=False)
    # default = lambda self: self.env.ref('ejad_erp_hr.dynamic_workflow_stage_data_0').id
    have_secondary_stage = fields.Boolean(
        string="have secondary stage", compute="check_current_stage_have_secondary_stage"
        )
    current_second_stage = fields.Many2one(
        "dynamic.workflow.stage", string="المرحلة الفرعية الحالية", tracking=True
        )
    secondary_stage_ids = fields.One2many(related="stage_id.secondary_stage_ids", string="Secondary stages",
                                         )

    is_stage_success = fields.Boolean(related="stage_id.is_success_type")
    is_stage_refuse = fields.Boolean(related="stage_id.is_refuse_type")
    is_stage_first = fields.Boolean(related="stage_id.is_first_type")
    is_stage_cancel = fields.Boolean(related="stage_id.is_cancel_type")

    next_stage_permission = fields.Boolean("Next stage permission", compute="check_next_stage_permission",)
    next_second_stage_permission = fields.Boolean("Next stage Second permission", compute="check_next_stage_permission",
                                                )
    precedent_stage_permission = fields.Boolean(
        "Precedent stage permission", compute="check_precedent_stage_permission"
        )
    precedent_second_stage_permission = fields.Boolean(
        "Precedent stage Second permission", compute="check_precedent_stage_permission"
        )
    refuse_stage_permission = fields.Boolean("Refuse stage permission", compute="check_refuse_stage_permission",
                                            )

    designation = fields.Boolean(related="stage_id.designation")
    designation_secondary_stage = fields.Boolean(related="current_second_stage.designation")

    designation_office = fields.Boolean(related="stage_id.designation_office")
    designation_office_secondary_stage = fields.Boolean(related="current_second_stage.designation_office",
                                                       )

    related_stages = fields.Char(
        compute="_compute_related_stages", help="Technical filed used for workflow stage display"
        )
    related_secondary_stages = fields.Char(
        compute="_compute_related_stages", help="Technical filed used for workflow stage display"
        )

    is_assign_employee_allowed = fields.Boolean(compute="_compute_is_assign_employee_allowed")
    is_assign_office_allowed = fields.Boolean(compute="_compute_is_assign_office_allowed")
    is_refuse_action_allowed = fields.Boolean(compute="_compute_is_refuse_action_allowed")
    is_return_action_allowed = fields.Boolean(compute="_compute_is_return_action_allowed")
    is_workflow_next_allowed = fields.Boolean(compute="_compute_is_workflow_next_allowed")
    is_workflow_previous_allowed = fields.Boolean(compute="_compute_is_workflow_previous_allowed")
    date_deadline = fields.Date(string="Achievement Deadline", readonly=True)
    deadline_exceeded = fields.Boolean(string="Deadline Exceeded", compute="_compute_deadline_exceeded")
    delayed = fields.Date(string="Achievement Deadline delay", readonly=True)
    auto_workflow_next_after_deadline = fields.Boolean(
        string="Pass to next stage automatically after deadline?", readonly=True
        )
    is_allow_move_other_stage = fields.Boolean("إمكانية الانتقال الى مرحلة اخري")
    company_notes = fields.Char("ملاحظات شركة التوثيق")

    current_employee = fields.Many2one(
        "hr.employee", string="Current employee", compute="find_current_employee", tracking=True
        )
    current_department = fields.Many2one(
        "hr.department", string="current department", compute="find_current_department", tracking=True
        )

    current_user = fields.Many2one("hr.employee", string="Current user", readonly=True, copy=False)
    employee_assigned = fields.Boolean(
        string="Employee assigned", compute="current_employee_is_assigned", tracking=True)

    """
    This field computes the users that do have access to the current request by the fact of being a member of
    the current or prior stages.
    """
    stage_security_users_ids = fields.Many2many('res.users', compute="_compute_stage_security_users_ids", store=True,
                                                )

    def check_next_stage_permission(self):
        user_id = self.env.user
        next_stage = self.stage_id
        # check if user have permission to pass to this stage
        employee_obj = self.env["hr.employee"].search([("user_id", "=", user_id.id)])
        if (
                user_id in [employee_id.user_id for employee_id in next_stage.employee_ids]
                or employee_obj.department_id in next_stage.department_ids
                or user_id.groups_id in next_stage.group_ids
                or next_stage.group_ids in user_id.groups_id
        ):
            self.next_stage_permission = True

        next_second_stage = self.current_second_stage
        if (
                user_id in [employee_id.user_id for employee_id in next_second_stage.employee_ids]
                or employee_obj.department_id in next_second_stage.department_ids
                or user_id.groups_id in next_second_stage.group_ids
                or next_second_stage.group_ids in user_id.groups_id
        ):
            self.next_second_stage_permission = True

    def check_refuse_stage_permission(self):
        user_id = self.env.user
        refuse_stage = self.stage_ids.search([("is_refuse_type", "=", True)], limit=1)
        employee_obj = self.env["hr.employee"].search([("user_id", "=", user_id.id)])

        if (
                user_id in [employee_id.user_id for employee_id in refuse_stage.employee_ids]
                or employee_obj.department_id in refuse_stage.department_ids
                or user_id.groups_id in refuse_stage.group_ids
                or refuse_stage.group_ids in user_id.groups_id
        ):
            self.refuse_stage_permission = True

    def workflow_previous(self):
        self.ensure_one()
        self._on_workflow_previous()
        previous_stage_ids = self._get_previous_stages()
        context = {"previous_stage_ids": previous_stage_ids, "default_holidays_id": self.id}
        context.update(self.env.context)

        return {
            "type": "ir.actions.act_window",
            "name": "Previous Stage",
            "res_model": "dynamic.workflow.holidays.stage.previous.wizard",
            "view_mode": "form",
            "target": "new",
            "context": context,
        }

    @api.depends("stage_id")
    def check_current_stage_have_secondary_stage(self):
        for rec in self:
            if rec.secondary_stage_ids:
                rec.have_secondary_stage = True
            else:
                rec.have_secondary_stage = False

    @api.depends("holiday_status_id","holiday_status_id.is_sick_holiday")
    def get_project_type(self):
        for rec in self:
            print(rec.holiday_status_id)
            if rec.holiday_status_id.is_sick_holiday:
                rec.project_type = self.env.ref('ejad_erp_hr.sick_holidays_project_type_data').id
            else:
                rec.project_type = self.env.ref('ejad_erp_hr.holidays_project_type_data').id

    @api.depends("date_deadline")
    def _compute_deadline_exceeded(self):
        today = fields.Date.from_string(fields.Date.context_today(self))
        for rec in self:
            if rec.date_deadline:
                date_deadline = fields.Date.from_string(rec.date_deadline)
                if date_deadline < today:
                    rec.deadline_exceeded = True

    @api.depends()
    def current_employee_is_assigned(self):
        for rec in self:
            if self.env.user.id == rec.current_user.user_id.id:
                rec.employee_assigned = True
            else:
                rec.employee_assigned = False

    def _compute_related_stages(self):
        for rec in self:
            visible_stages = rec._get_visible_stages()
            rec.related_stages = str(visible_stages and visible_stages.ids or [])
            related_secondary_stages = rec.secondary_stage_ids.ids
            rec.related_secondary_stages = str(related_secondary_stages)

    def find_current_employee(self):
        for rec in self:
            rec.current_employee = self.env["hr.employee"].search([("user_id", "=", self.env.user.id)])

    def find_current_department(self):
        for rec in self:
            rec.current_department = self.env["hr.employee"].search(
                [("user_id", "=", self.env.user.id)]).department_id

    def _compute_stage_ids(self):
        for rec in self:
            rec.stage_ids = rec.project_type.stage_ids.ids

    def _get_visible_stages(self):
        self.ensure_one()
        return self.stage_ids.filtered(
            lambda r: r.is_first_type == False and r.is_refuse_type == False and r.holidays_state in (
            'confirm', 'direct_manager_approve', 'hr_checker', 'validate'))

    def _compute_is_assign_employee_allowed(self):
        for rec in self:
            if (
                    not rec.stage_id
                    or rec.is_stage_refuse
                    or rec.is_stage_success
                    or (rec.have_secondary_stage and not rec.designation_secondary_stage)
                    or (not rec.have_secondary_stage and not rec.designation)
            ):
                rec.is_assign_employee_allowed = False
                continue
            if rec.designation_secondary_stage and rec.current_employee not in rec.current_second_stage.employee_ids:
                rec.is_assign_employee_allowed = False
                continue
            rec.is_assign_employee_allowed = True

    def _compute_is_assign_office_allowed(self):
        for rec in self:
            if (
                    not rec.stage_id
                    or rec.is_stage_refuse
                    or rec.is_stage_success
                    or (rec.have_secondary_stage and not rec.designation_office_secondary_stage)
                    or (not rec.have_secondary_stage and not rec.designation_office)
            ):
                rec.is_assign_office_allowed = False
                continue
            if rec.designation_office_secondary_stage and rec.current_employee not in rec.current_second_stage.employee_ids:
                rec.is_assign_office_allowed = False
                continue
            rec.is_assign_office_allowed = True

    def _compute_is_refuse_action_allowed(self):
        for rec in self:
            if (
                    not rec.stage_id
                    or rec.is_stage_refuse
                    or rec.is_stage_success
                    # [FIXME] shaimaa or not rec.refuse_stage_permission
                    or (not rec.is_assign_employee_allowed and not rec.is_workflow_next_allowed)
            ):
                rec.is_refuse_action_allowed = False
            else:
                rec.is_refuse_action_allowed = True

    def _compute_is_return_action_allowed(self):
        for rec in self:
            if (
                    not rec.stage_id
                    or rec.is_stage_first
                    or rec.is_stage_refuse
                    or rec.is_stage_success
                    or not rec.stage_id.is_return_to_investor_stage
            ):
                rec.is_return_action_allowed = False
            else:
                rec.is_return_action_allowed = True

    def _compute_is_workflow_next_allowed(self):
        for rec in self:
            if (
                    rec.is_stage_refuse
                    or rec.is_stage_success
                    or not rec.stage_id
                    or rec.is_assign_employee_allowed
                    # [FIXME] shaimaa or (not rec.next_stage_permission and not rec.next_second_stage_permission)
            ):
                rec.is_workflow_next_allowed = False
            else:
                rec.is_workflow_next_allowed = True

    def _compute_is_workflow_previous_allowed(self):
        for rec in self:
            if not rec._get_previous_stages():
                rec.is_workflow_previous_allowed = False
            else:
                if (
                        rec.is_stage_first
                        or rec.is_stage_refuse
                        or rec.is_stage_success
                        or not rec.stage_id
                        or (not rec.is_workflow_next_allowed and not rec.is_assign_employee_allowed)
                ):
                    rec.is_workflow_previous_allowed = False
                else:
                    rec.is_workflow_previous_allowed = True

    @api.depends('stage_ids', 'stage_id')
    def _compute_stage_security_users_ids(self):
        users_related = []

        for stage in self.stage_ids:
            if self.stage_id.sequence >= stage.sequence:
                _logger.debug('Stage ' + str(stage) + ' is prior or equal to current one.')
                for employee in stage.employee_ids:
                    users_related.append(employee.user_id.id)

        if users_related:
            self.stage_security_users_ids = [(6, False, users_related)]

        return True

    def workflow_init(self):
        self.ensure_one()
        if not self.stage_id:
            self.stage_id = self.stage_ids and self.stage_ids[0] or False

    @api.model
    def _get_first_stage(self):
        stage_ids = self.env['workflow.project.type'].search([("code", "=", 'contract')]).stage_ids
        if stage_ids:
            return stage_ids[0]
        else:
            return False

    def _get_previous_stages(self):
        self.ensure_one()
        previous_stage_ids = []
        for stage in self._get_visible_stages():
            if stage != self.stage_id:
                previous_stage_ids.append(stage.id)
            else:
                break
        if self.secondary_stage_ids:
            for stage in self.secondary_stage_ids:
                if stage != self.current_second_stage:
                    previous_stage_ids.append(stage.id)
                else:
                    break
        return previous_stage_ids

    def _on_workflow_next(self):
        self.ensure_one()
        self.write(
            {

                "date_deadline": False,

                "current_user": False,
                "auto_workflow_next_after_deadline": False,
            }
        )
        self.set_value_to_date_deadline_stage()

    def _on_workflow_previous(self):
        self.ensure_one()
        self.write(
            {

                "date_deadline": False,

                "current_user": False,
                "auto_workflow_next_after_deadline": False,
            }
        )
        self.set_value_to_date_deadline_stage()

    def set_value_to_date_deadline_stage(self):
        self.ensure_one()
        if not self.designation:
            if not self.current_second_stage:
                achievement_duration = self.stage_id.achievement_duration
            else:
                achievement_duration = max(
                    self.stage_id.achievement_duration,
                    self.current_second_stage.achievement_duration,
                )
            today = fields.Date.from_string(fields.Date.context_today(self))
            today_ds = datetime.now().replace(second=0, microsecond=0)
            today_ds.strftime("%d/%m/%Y %H:%M:%S")
            check_day_in_weekdays = convert_date_to_dayinweek(str(today_ds))
            if check_day_in_weekdays == 'Thursday':
                achievement_duration = achievement_duration + 2
            self.date_deadline = today + relativedelta(days=achievement_duration)

    def workflow_next(self):
        self.ensure_one()

        self._on_workflow_next()

        if self.secondary_stage_ids:
            return self.workflow_next_secondary_stage()

        return self.workflow_next_stage()

    def action_move_other_stage(self):
        self.ensure_one()
        if self.is_allow_move_other_stage:
            self._on_workflow_next()
            self.current_second_stage = self.current_second_stage.parent_id.id
            user_id = self.env.user
            employee_obj = self.env["hr.employee"].sudo().search([("user_id", "=", user_id.id)])

    def workflow_next_stage(self):
        stage_ids = self.stage_ids.filtered(lambda r: r.is_refuse_type == False)
        # search and go to the next stage
        for stage, value in enumerate(stage_ids, 1):
            if self.stage_id.id == value.id:
                if self.stage_ids[stage - 1].send_request_to_direct_manager:
                    try:
                        if self.env.user.employee_ids.parent_id:
                            self.stage_id = stage_ids[stage]
                            self.current_user = self.env.user.employee_ids.parent_id
                            if self.secondary_stage_ids:
                                self.current_second_stage = self.secondary_stage_ids[0].id
                        else:
                            raise Exception
                    except Exception as e:
                        raise ValidationError("يجب إسناد مدير مباشر للموظف الحالي.")
                    break
                else:
                    if self.state == 'draft':
                        self.action_confirm()
                        self.stage_id = stage_ids[stage]

                    elif self.state == 'hr_checker':
                        self.action_approve_hr_manger()
                        stage_id = self.stage_ids.filtered(lambda r: r.holidays_state == self.state)
                        self.stage_id = stage_id.id
                    else:
                        self.stage_id = stage_ids[stage]
                        if stage_ids[stage].holidays_state:
                            self.state = stage_ids[stage].holidays_state

                    if self.secondary_stage_ids:
                        self.current_second_stage = self.secondary_stage_ids[0].id

                    break

    def workflow_next_secondary_stage(self):
        stage_ids = self.secondary_stage_ids

        # search and go to the next stage
        if stage_ids and not self.current_second_stage:
            self.current_second_stage = stage_ids[0]
        for stage, value in enumerate(stage_ids, 1):
            if self.current_second_stage.id == value.id:
                if stage != len(stage_ids):
                    if stage_ids[stage - 1].send_request_to_direct_manager:
                        try:
                            if self.env.user.employee_ids.parent_id:
                                self.current_second_stage = stage_ids[stage]
                                self.current_user = self.env.user.employee_ids.parent_id
                            else:
                                raise Exception
                        except Exception as e:
                            raise ValidationError("يجب إسناد مدير مباشر للموظف الحالي.")
                    else:
                        self.current_second_stage = stage_ids[stage]
                    break
                else:
                    self.workflow_next_stage()
                    user_id = self.env.user

                break

    def workflow_prev_stage(self):
        stage_ids = self.stage_ids
        # search and go to the next stage
        for stage, value in enumerate(stage_ids, 1):
            if self.stage_id.id == value.id:
                self.stage_id = stage_ids[stage - 2]

                break

    """
    End workflow ( المراحل )
    """

class HRHolidaysReturn(models.Model):
    _name = 'hr.leave.return'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "طلب مباشرة العمل"

    # message = fields.Char(compute="compute_message")
    name = fields.Char(tracking=True)
    hr_leave_id = fields.Many2one('hr.leave', string="الأجازة", tracking=True)
    employee_id = fields.Many2one(related='hr_leave_id.employee_id', string="الموظف", tracking=True)
    department_id = fields.Many2one(related='hr_leave_id.department_id')
    holiday_status_id = fields.Many2one(related='hr_leave_id.holiday_status_id', tracking=True)
    request_return_date = fields.Date(string='تاريخ مباشرة العمل' ,required=True ,tracking=True)
    request_date_from = fields.Date(related='hr_leave_id.request_date_from')
    request_date_to = fields.Date(related='hr_leave_id.request_date_to')
    number_of_days = fields.Float(related='hr_leave_id.number_of_days')
    description = fields.Char(related='hr_leave_id.name',store=True)
    refuse_message = fields.Text("Refuse message", tracking=True)
    user_id = fields.Many2one('res.users', string='User', related='employee_id.user_id', related_sudo=True,
                              compute_sudo=True, store=True, default=lambda self: self.env.uid, readonly=True)
    leave_validation_type = fields.Selection(string='Validation Type', related='holiday_status_id.leave_validation_type', readonly=False)
    days_off_add = fields.Float(required=True, string='عدد الأيام خصم /إضافة')
    action_type = fields.Selection([
        ('add_allocation', 'إضافة رصيد'),
        ('remove_allocation', 'خصم رصيد'),
        ('no_action', 'لا يوجد إجراء'),

    ], string='Status', tracking=True, copy=False)

    state = fields.Selection([
        ('draft', 'الموظف'),
        ('cancel', 'Cancelled'),
        ('direct_manager', 'المدير المباشر'),
        ('hr_approve', 'مسؤول الموارد البشرية'),
        ('validate', 'تم الموافقة'),
        ('refuse', 'تم الرفض'),

    ], string='Status', readonly=True, tracking=True, copy=False, default='draft')

    @api.constrains('action_type')
    def _constrain_days_off_add(self):
        for record in self:
            if record.action_type in ('add_allocation','remove_allocation'):
                if record.days_off_add <= 0:
                   raise ValidationError(_("لابد من إدخال عدد الأيام المضافة /المخصومة من الرصيد"))

    def get_users(self, group_name):
        user_ids = []
        users = self.env['res.users'].search([])
        for user in users:
            if user.has_group(group_name):
                user_ids.append(user.id)
        if len(user_ids) > 0:
            return user_ids
        else:
            raise ValidationError(('لم يتم تخصيص الشخص المعني للمرحلة القادمة'))

    def action_direct_manager(self):
        for rec in self:
            if rec.employee_id.sudo().parent_id.user_id:
                rec.activity_feedback(['mail.mail_activity_data_todo'],
                                      feedback='تم اكمال المهمة بنجاح شكرا لك')
                rec.activity_schedule('mail.mail_activity_data_todo',
                                      user_id=rec.employee_id.sudo().parent_id.user_id.id,
                                      res_id=rec.id)
            rec.write({'state': 'direct_manager'})

    def action_confirm(self):
        for rec in self:
            self.write({'state': 'hr_approve'})
            for user in rec.get_users('ejad_erp_hr.group_hr_holiday_specialist'):
                rec.activity_feedback(['mail.mail_activity_data_todo'],
                                      feedback='تم اكمال المهمة بنجاح شكرا لك')
                rec.activity_schedule('mail.mail_activity_data_todo',
                                      user_id=user,
                                      res_id=rec.id)
        return True

    def action_validate(self):
        for rec in self:
            rec.write({'state': 'validate'})
            rec.hr_leave_id.sudo().write({'leave_return_id': rec.id})

            rec.activity_feedback(['mail.mail_activity_data_todo'],
                                   feedback='تم اكمال المهمة بنجاح شكرا لك')
            if rec.action_type in ('add_allocation','remove_allocation'):
                exist_allocate_record = self.env['hr.leave.allocation'].search(
                    [('employee_id', '=', rec.employee_id.id),
                     ('holiday_status_id', '=', rec.holiday_status_id.id),
                     ], limit=1)

                if exist_allocate_record:
                   if rec.action_type == 'add_allocation':
                        updated_allocation_days = exist_allocate_record.number_of_days + rec.days_off_add
                        exist_allocate_record.number_of_days = updated_allocation_days
                        exist_allocate_record.message_post(body=('تم إضافة عدد أيام : %s الى الرصيد لمباشرة العمل قبل موعد انتهاء الإجازة') % (rec.days_off_add),
                                                           message_type='email', subject=rec.name)
                   if rec.action_type == 'remove_allocation':
                        updated_allocation_days = exist_allocate_record.number_of_days - rec.days_off_add
                        if exist_allocate_record.number_of_days < rec.days_off_add:
                            raise ValidationError(('الرصيد غير كافى للخصم . الرصيد الحالى : %s') % (exist_allocate_record.number_of_days))
                        else:
                            exist_allocate_record.number_of_days = updated_allocation_days
                            exist_allocate_record.message_post(body=('تم خصم عدد أيام : %s من الرصيد لتأخر معاد مباشرة العمل') % (rec.days_off_add), message_type='email', subject=rec.name)
                   else:
                       continue
                else:
                    continue

        return True

    def action_draft(self):
        self.write({'state': 'draft'})
        self.activity_feedback(['mail.mail_activity_data_todo'],
                              feedback='تم اكمال المهمة بنجاح شكرا لك')

        self.activity_schedule('mail.mail_activity_data_todo',
                              user_id=self.employee_id.user_id.id,
                              res_id=self.id)
        return True