# -*- coding: utf-8 -*-

from odoo import models
import dateutil.parser


class TranscationstoExcell(models.AbstractModel):
    _name = 'report.ejad_erp_administrative_communications.tran_xlsx'
    _description = 'Report tran_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def get_lines(self, info):
        domain = []
        if info['date_from']:
            domain.append(('date', '>=', info['date_from']))
        if info['date_to']:
            domain.append(('date', '<=', info['date_to']))

        if info['external_partner_ids']:
            domain.append(('external_partner_ids', 'in', info['external_partner_ids']))

        if info['ac_operation_ids']:
            # domain = []
            domain.append(('id', 'in', info['ac_operation_ids']))
            operations_ids = self.env['ac.operation'].search(domain)
            return operations_ids

        if info['report_type'] == 'global_inbox':
            domain.append(('type', '=', 'in'))
            operations_ids = self.env['ac.operation'].search(domain)
            return operations_ids

        elif info['report_type'] == 'global_outbox':
            domain.append('|')
            domain.append(('type', '=', 'out'))
            domain.append(('is_global_outbox', '=', True))
            operations_ids = self.env['ac.operation'].search(domain)
            return operations_ids

        elif info['report_type'] == 'internal':
            domain.append(('type', '=', 'internal'))
            operations_ids = self.env['ac.operation'].search(domain)
            return operations_ids

        elif info['report_type'] == 'saved':
            domain.append(('is_saved', '=', True))
            operations_ids = self.env['ac.operation'].search(domain)
            return operations_ids

        elif info['report_type'] == 'late':
            # domain.append()
            operations_ids = self.env['ac.operation'].search(domain)
            return operations_ids

        elif info['report_type'] == 'transfer':
            domain.append(('type', '=', 'transfer'))
            operations_ids = self.env['ac.operation.move'].search(domain)
            return operations_ids

        elif info['report_type'] == 'all':
            operations_ids = self.env['ac.operation'].search(domain)
            return operations_ids
        else:
            return []

    def generate_xlsx_report(self, workbook, data, lines):
        records = self.get_lines(data['form'])
        host = self.env.user.company_id.host or 'localhost:8069'
        sheet = workbook.add_worksheet("كشف المعاملات")
        sheet.right_to_left()
        sheet.set_column(0, 3, 10)
        sheet.set_column(4, 15, 12)
        format0 = workbook.add_format(
            {'font_size': 20, 'align': 'center', 'valign': 'vcenter', 'right': True, 'left': True, 'bottom': True,
             'top': True,
             'bold': True,
             'underline': True,
             'italic': True,
             'font_color':'blue',
             'bg_color': 'F8F8FF',})
        format1 = workbook.add_format(
            {'font_size': 16, 'align': 'center', 'valign': 'vcenter', 'right': True, 'left': True, 'bottom': True,
             'top': True,
             'bold': True})
        format2 = workbook.add_format(
            {'font_size': 10, 'align': 'center', 'valign': 'vcenter', 'right': True, 'left': True, 'bottom': True,
             'top': True,
             'bold': True})
        sheet.merge_range(0, 0, 1, 14, 'كشف المعاملات', format0)
        sheet.set_column(0, 3, 10)
        sheet.set_column(4, 15, 12)
        sheet.write(2, 0, 'م', format1)
        sheet.write(2, 1, 'رقم المعاملة', format1)
        sheet.write(2, 2, 'تاريخ المعاملة', format1)
        sheet.write(2, 3, 'رقم الوارد', format1)
        sheet.write(2, 4, 'تاريخ الوارد', format1)
        sheet.write(2, 5, 'الجهة', format1)
        sheet.write(2, 6, 'الموضوع', format1)
        sheet.write(2, 7, 'تاريخ الموضوع', format1)
        sheet.write(2, 8, 'التوجيه', format1)
        sheet.write(2, 9, 'تاريخ التوجيه', format1)
        sheet.write(2, 10, 'آخر وقت للتنفيذ', format1)
        sheet.write(2, 11, 'الحالة', format1)
        sheet.write(2, 12, 'الإفادة', format1)
        sheet.write(2, 13, 'رقم الصادر', format1)
        sheet.write(2, 14, 'تاريخ الصادر', format1)
        sheet.write(2, 15, 'مستوى السرية', format1)

        row = 3
        c = 1
        action_id = self.env.ref('ejad_erp_administrative_communications.action_ac_operation_in').id
        for rec in records:
            llink = host + '/web#id=' + str(rec.id) + '&view_type=form&action=' + str(action_id) + '&model=ac.operation'
            sheet.write(row, 0, c or '', format2)
            sheet.write(row, 1, rec.incoming_no or '', format2)
            sheet.write(row, 2, rec.incoming_date or '', format2)
            partner = ''
            for p in rec.external_partner_ids:
                partner += (p.name + '، ')
            if partner:
                partner = partner[0:(len(partner) - 2)]
            sheet.write(row, 3, rec.name or '', format2)
            sheet.write(row, 4, rec.date and str(dateutil.parser.parse(str(rec.date)).date()) or '', format2)
            sheet.write(row, 5, partner or '', format2)
            sheet.write(row, 6, rec.subject or '', format2)
            sheet.write(row, 7, rec.subject_date and str(dateutil.parser.parse(str(rec.subject_date)).date()) or '', format2)
            sheet.write(row, 8, rec.directing or '', format2)
            sheet.write(row, 9, rec.directing_date and str(dateutil.parser.parse(str(rec.directing_date)).date()) or '', format2)
            sheet.write(row, 10, rec.deadline_date and str(dateutil.parser.parse(str(rec.deadline_date)).date()) or '', format2)
            deadline_state = rec.deadline_state
            security = rec.security
            sheet.write(row, 11, deadline_state and dict(rec.fields_get(allfields=['deadline_state'])['deadline_state']['selection'])[deadline_state] or '', format2)
            sheet.write_url(row, 12, llink or '', format2, string='الرابط')
            sheet.write(row, 13, rec.outbound_no or '', format2)
            sheet.write(row, 14, rec.outbound_date and str(dateutil.parser.parse(str(rec.outbound_date)).date()) or '', format2)
            sheet.write(row, 15, security and
                       dict(rec.fields_get(allfields=['security'])['security']['selection'])[security] or '', format2)
            row += 1
            c += 1
