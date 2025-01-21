from odoo import models, fields, api

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    def name_get(self):
        result = []
        for employee in self:
            name = f'[{employee.code}] {employee.name}' if employee.code else employee.name
            result.append((employee.id, name))
        return result

    @api.model
    def _name_search(self, name='', args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('name', operator, name), ('code', operator, name)]
        return self._search(domain + args, limit=limit, access_rights_uid=name_get_uid)


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    # Override the employee_id field to change its display
    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee',
        required=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
    )

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        if self.employee_id:
            # Get the latest contract for the employee
            contract = self.env['hr.contract'].search([
                ('employee_id', '=', self.employee_id.id),
                ('state', 'in', ['open', 'near_end']),  # Only get active contracts
            ], order='create_date desc', limit=1)
            
            if contract:
                self.contract_id = contract.id
            else:
                # If no active contract found, try to find the most recent contract in any state
                contract = self.env['hr.contract'].search([
                    ('employee_id', '=', self.employee_id.id),
                ], order='create_date desc', limit=1)
                
                if contract:
                    self.contract_id = contract.id
