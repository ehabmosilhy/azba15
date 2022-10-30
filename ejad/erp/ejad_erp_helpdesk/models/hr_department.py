# -*- coding: utf-8 -*-

import logging
from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class HRDepartment(models.Model):
    _inherit = 'hr.department'

    type = fields.Selection([
                ('any', 'رئاسة الجامعة'),
                ('ean13', 'وكالة'),
                ('ean8', 'عمادة'),
                ('top_management', 'إدارة عامة'),
                ('management', 'إدارة'),
                ('center', 'مركز'),
                ('dept', 'قسم'),
                ('unit', 'وحدة'),
        ], string='النوع')
