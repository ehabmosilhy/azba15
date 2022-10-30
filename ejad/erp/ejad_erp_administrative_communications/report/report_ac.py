# -*- coding: utf-8 -*-

from odoo import api, models, _
from odoo.exceptions import UserError


class ReportAC(models.AbstractModel):
    _name = 'report.ejad_erp_administrative_communications.report_ac'
    _description = 'Report AC'

    @api.model
    def _get_report_values(self, docids, data=None):
        title = ''

        if data['form']['report_type'] == 'global_inbox':
            title = 'تقرير معاملات الوارد العام'

        if data['form']['report_type'] == 'global_outbox':
            title = 'تقرير معاملات الصادر العام'

        if data['form']['report_type'] == 'internal':
            title = 'تقرير المعاملات الداخلية'

        if data['form']['report_type'] == 'saved':
            title = 'تقرير المعاملات المحفوظة'

        if data['form']['report_type'] == 'late':
            title = 'تقرير المعاملات المتأخرة'

        if data['form']['report_type'] == 'transfer':
            title = 'تقرير قائمة الإحالات'

        if data['form']['report_type'] == 'all':
            title = 'تقرير إجمالي المعاملات'

        if len(self.get_lines(data.get('form'))) == 0:
            raise UserError(_("لا توجد معاملات حسب هذه المعطيات .."))

        return {
            'title': title,
            'data': data['form'],
            'lines': self.get_lines(data.get('form')),
        }

    @api.model
    def get_lines(self, info):
        domain = [('date', '>=', info['date_from']), ('date', '<=', info['date_to'])]

        if info['external_partner_ids']:
            domain.append(('external_partner_ids', 'in', info['external_partner_ids']))

        if info['report_type'] == 'global_inbox':
            domain.append(('type', '=', 'in'))
            operations_ids = self.env['ac.operation'].search(domain)
            return operations_ids

        if info['report_type'] == 'global_outbox':
            domain.append('|')
            domain.append(('type', '=', 'out'))
            domain.append(('is_global_outbox', '=', True))
            operations_ids = self.env['ac.operation'].search(domain)
            return operations_ids

        if info['report_type'] == 'internal':
            domain.append(('type', '=', 'internal'))
            operations_ids = self.env['ac.operation'].search(domain)
            return operations_ids

        if info['report_type'] == 'saved':
            domain.append(('is_saved', '=', True))
            operations_ids = self.env['ac.operation'].search(domain)
            return operations_ids

        if info['report_type'] == 'late':
            # domain.append()
            operations_ids = self.env['ac.operation'].search(domain)
            return operations_ids

        if info['report_type'] == 'transfer':
            domain.append(('type', '=', 'transfer'))
            operations_ids = self.env['ac.operation.move'].search(domain)
            return operations_ids

        if info['report_type'] == 'all':
            operations_ids = self.env['ac.operation'].search(domain)
            return operations_ids
