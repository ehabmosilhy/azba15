# -*- encoding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    @api.model
    def create(self, vals):
        if 'user_id' in vals:
            user_id = self.env['res.users'].search([('id', '=', vals['user_id'])])
            if len(user_id.employee_ids) >= 1:
                raise UserError(
                    'المستخدم ذات الصلة عنده موظف مرتبط به ..!\n كل مستخدم للنظام يجب أن يكون مرتبط به موظف واحد فقط .!')
        res = super(HrEmployee, self).create(vals)
        return res

    
    def write(self, vals):
        #if 'user_id' in vals:
        #    user_id = self.env['res.users'].search([('id', '=', vals['user_id'])])
        #    if len(user_id.employee_ids) >= 1:
        #        raise UserError(
        #            'المستخدم ذات الصلة عنده موظف مرتبط به ..!\n كل مستخدم للنظام يجب أن يكون مرتبط به موظف واحد فقط .!')
        res = super(HrEmployee, self).write(vals)
        return res


class ResUsers(models.Model):
    _inherit = "res.users"

    # employee_id = fields.Many2one('hr.employee', compute="one_related_employee")
    department_id = fields.Many2one(related="employee_id.department_id", string="الإدارة")


    # def one_related_employee(self):
    #     if self.employee_ids:
    #         self.employee_id = self.employee_ids[0]
