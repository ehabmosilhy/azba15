# -*- coding: utf-8 -*-

import logging
from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class HRDepartment(models.Model):
    _inherit = 'hr.department'

    type = fields.Selection([
                ('any', 'رئاسة'),
                ('ean13', 'وكالة'),
                ('ean8', 'عمادة'),
                ('top_management', 'إدارة عامة'),
                ('management', 'إدارة'),
                ('center', 'مركز'),
                ('dept', 'قسم'),
                ('unit', 'وحدة'),
        ], string='النوع')
    code = fields.Integer(copy=False, string='الرمز')
    sequence_id = fields.Many2one('ir.sequence', string='اعداد الرقم المتسلسل', copy=False)

    _sql_constraints = [
        ('department_code', 'UNIQUE (code)', 'لا يمكن تكرار الرمز'),
    ]

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=10000):
        args = args or []
        domain = []
        if name and name.isdigit():
            domain = ['|', '|', ('name', 'ilike', name), ('complete_name', 'ilike', name), ('code', '=', int(name))]
        elif name:
            domain = ['|', ('name', 'ilike', name), ('complete_name', 'ilike', name)]
        dep = self.search(domain + args, limit=limit)
        return dep.name_get()
