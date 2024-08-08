# -*- coding: utf-8 -*-

from itertools import groupby

from odoo import models, _
from odoo.exceptions import UserError


class Account(models.Model):
    _inherit = 'account.move'

    def action_send_whatsapp(self):
        report = self.env.ref('custom_invoice_templates.report_azbah_invoice_rep')
        pdf_content, content_type = report._render_qweb_pdf(self.ids)
        report_name = 'Invoice_Report.pdf'

        return {
            'type': 'ir.actions.report',
            'report_name': report.report_name,
            'report_type': 'qweb-pdf',
            'data': {'ids': self.ids},
            'report_file': report_name,
            'context': {'active_model': 'account.move', 'active_id': self.id, 'model': 'account.move', 'id': self.id}
        }


