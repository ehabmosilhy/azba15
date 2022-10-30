# -*- coding: utf-8 -*-

import logging
from odoo import api, fields, models, _
from odoo.tools import float_compare
from odoo.exceptions import UserError, AccessError, ValidationError

_logger = logging.getLogger(__name__)


class SalaryBonus(models.Model):
    _name = 'salary.bonus'
    _description = 'Salary Bonus'


    def employee_yearly_salary_bonus(self):
        contracts = self.env['hr.contract'].search([])
        for contract in contracts:
            current_employee_salary_type = contract.grade_level_id.grade_id.grade_type_id
            current_employee_grade = contract.grade_level_id
            current_level_sequence = contract.grade_level_id.level_sequence
            next_grade = self.env['hr.grade.level'].search(
                [('grade_type_id', '=', current_employee_salary_type.id),
                 ('level_sequence', '=', current_level_sequence),
                 ('gross', '>', current_employee_grade.gross),
                 ], limit=1)

            # next_grade = self.env['hr.grade.level'].search(
            #     ['&', '&', '&',
            #      ('grade_type_id', '=', current_employee_salary_type.id),
            #      ('id', '!=', current_employee_grade.id),
            #      ('gross', '>', current_employee_grade.gross),
            #      '|',
            #      ('sequence', '>', current_employee_grade.sequence),
            #      '&',
            #      ('sequence', '=', current_employee_grade.sequence),
            #      ('id', '>', current_employee_grade.id),
            #      ], limit=1)
            if next_grade:
                print(contract.employee_id.name)
                print(next_grade.name)
                contract.grade_level_id = next_grade.id
                #contract.hosing_allowancme= self.onchange_house_allow1(contract.has_housing_allow, contract.wage)


    def employee_update_housing(self):
        contracts = self.env['hr.contract'].search([('has_housing_allow', '=', True), ('is_exceptional', '!=', True)])
        for contract in contracts:
            if contract.has_housing_allow and contract.wage:
                housing_allow = contract.wage * 3 / 12
                if housing_allow > 2000:
                    housing_allow = 2000
                elif 1000 > housing_allow > 0:
                    housing_allow = 1000
                contract.hosing_allowancme = housing_allow
            else:
                contract.hosing_allowancme = 0.00

    def onchange_house_allow1(self, has_housing_allow=False, wage=0.00):
        if has_housing_allow:
            housing_allow = wage * 3 / 12

            if housing_allow > 2000:
                housing_allow = 2000
            elif 1000 > housing_allow > 0:
                housing_allow = 1000
            return housing_allow
        else:
            return 0.0