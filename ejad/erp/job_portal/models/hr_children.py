# See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class HrChildren(models.Model):
    _name = 'hr.employee.children'
    _description = "Employee's Children"

    name = fields.Char("Name", required=True)
    gender = fields.Selection(selection=[('male', 'Male'),
                              ('female', 'Female')],
                              string='Gender')
    date_of_birth = fields.Date("Date of Birth")
    employee_id = fields.Many2one('hr.employee', "Employee")
