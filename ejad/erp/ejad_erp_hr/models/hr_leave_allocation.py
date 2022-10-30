# -*- coding: utf-8 -*-

import logging

from datetime import datetime, time
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.addons.resource.models.resource import HOURS_PER_DAY
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.translate import _
from odoo.tools.float_utils import float_round

_logger = logging.getLogger(__name__)


class HolidaysAllocation(models.Model):
    """ Allocation Requests Access specifications: similar to leave requests """
    _name = "hr.leave.allocation"
    _inherit = ['hr.leave.allocation', 'mail.thread', 'mail.activity.mixin']

    state = fields.Selection([
        ('draft', 'To Submit'),
        ('cancel', 'Cancelled'),
        ('confirm', 'To Approve'),
        ('refuse', 'Refused'),
        ('validate1', 'Second Approval'),
        ('validate', 'Approved')
        ], string='Status', readonly=True, tracking=True, copy=False, default='draft',
        help="The status is set to 'To Submit', when an allocation request is created." +
        "\nThe status is 'To Approve', when an allocation request is confirmed by user." +
        "\nThe status is 'Refused', when an allocation request is refused by manager." +
        "\nThe status is 'Approved', when an allocation request is approved by manager.")

    def action_validate(self):
        current_employee = self.env.user.employee_id
        for holiday in self:
            if holiday.state not in ['confirm', 'validate1']:
                raise UserError(_('Allocation request must be confirmed in order to approve it.'))

            holiday.write({'state': 'validate'})
            if holiday.validation_type == 'both':
                holiday.write({'second_approver_id': current_employee.id})
            else:
                holiday.write({'first_approver_id': current_employee.id})

            holiday._action_validate_create_childs()
        self.activity_update()

        if self.employee_id:
            template_allocation_approve = self.env.ref("ejad_erp_hr.hr_allocation_approve_notify_employee_mail_template")

            try:

                self.env['mail.template'].sudo().browse(template_allocation_approve.id).send_mail(self.id)
                self.message_post(body=_("لقد تم الموافقة على منح رصيد أجازات %s") % (
                    self.employee_id.name), message_type='email',
                                  subject='لقد تم الموافقة على منح رصيد أجازات')
            except:
                pass
        return True

    def allocate_monthly_vacation(self):
        annual_holiday = self.env['hr.leave.type'].search([('is_annual_holiday', '=', True)], limit=1)
        if annual_holiday:

            employees = self.env['hr.employee'].search(
                [('active', '=', True), ('contract_type', 'in', ['management', 'staff'])])
            allocate_days = 0
            for employee in employees:

                if employee.contract_type == 'management':
                    allocate_days = annual_holiday.number_of_days_management

                elif employee.contract_type == 'staff':
                    allocate_days = annual_holiday.number_of_days_staff

                exist_allocate_record = self.env['hr.leave.allocation'].search(
                    [('employee_id', '=', employee.id),
                     ('holiday_status_id', '=', annual_holiday.id),
                     ], limit=1)

                if not allocate_days:
                    continue

                if exist_allocate_record:

                    updated_allocation_days = exist_allocate_record.number_of_days + allocate_days / 12
                    exist_allocate_record.number_of_days = updated_allocation_days

                else:
                    self.env['hr.leave.allocation'].create({
                        'employee_id': employee.id,
                        'number_of_days': allocate_days / 12,
                        'holiday_status_id': annual_holiday.id,
                        'state': 'validate',
                    })


    # def allocate_annual_vacation_for_sicetific(self):
    #     annual_holiday = self.env['hr.leave.type'].search([('is_annual_holiday', '=', True)], limit=1)
    #     if annual_holiday:
    #         allocate_days = 0
    #         allocate_days = annual_holiday.number_of_days_scientific
    #         employees = self.env['hr.employee'].search([('active', '=', True), ('contract_type', '=', 'sicetific')])
    #         annual_balance = self._get_remaining_leaves_for_annual(employees)
    #         for employee in employees:
    #             annual_balance_emp = annual_balance.get(employee.id, 0.0)
    #             exist_allocate_record = self.env['hr.leave'].search(
    #                 [('employee_id', '=', employee.id),
    #                  # type not found in odoo 13
    #                  # ('type', '=', 'add'),
    #                  ('holiday_status_id', '=', annual_holiday.id),
    #                  ], limit=1)
    #
    #             if exist_allocate_record:
    #                 updated_allocation_days = exist_allocate_record.number_of_days_temp - annual_balance_emp
    #                 balance = allocate_days - updated_allocation_days
    #                 updated_allocation_days_last = exist_allocate_record.number_of_days_temp + balance
    #                 exist_allocate_record.number_of_days_temp = updated_allocation_days_last
    #
    #             else:
    #                 allocation_request = self.env['hr.leave'].create({
    #                     'employee_id': employee.id,
    #                     'type': 'add',
    #                     'number_of_days_temp': allocate_days,
    #                     'holiday_status_id': annual_holiday.id,
    #                     'state': 'validate',
    #                 })
