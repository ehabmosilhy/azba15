# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
from odoo import api, fields, models, _
from odoo.tools import float_compare
from odoo.exceptions import UserError, AccessError, ValidationError
# import pyqrcode
import uuid
# import png

_logger = logging.getLogger(__name__)


class HrEmployeeSalaryLetterDestination(models.Model):
    _name = 'hr.employee.salary.letter.destination'
    _description = 'Hr Employee Salary Letter Destination'

    name = fields.Char('اسم الجهة', required=True)
    active = fields.Boolean(default=True, string='نشط')


class HrEmployeeSalaryLetter(models.Model):
    _name = 'hr.employee.salary.letter'
    _description = 'Hr Employee Salary Letter'

    template_id = fields.Many2one('mail.template', string='Template')
    contract_id = fields.Many2one('hr.contract', string="Contract")
    model_id = fields.Many2one('ir.model', string='Model', related='template_id.model_id', store=True)
    body_html = fields.Html('Body', sanitize=False)
    date = fields.Date(string='Date', default=fields.Date.context_today, required=True)
    destination_id = fields.Many2one('hr.employee.salary.letter.destination', string='Destinations')
    destination = fields.Char('Destination')
    destination2 = fields.Char('Destination by other Language')
    # with_header = fields.Boolean('With Header')
    field1 = fields.Char('Field1')
    field2 = fields.Char('Field2')
    field3 = fields.Char('Field3')

    qrcode = fields.Char(string="QR Code")
    qrcode_string = fields.Char(string="QR Code String")

    @api.model
    def create(self, vals):
        base_url = self.env["ir.config_parameter"].get_param("web.base.qrcode")
        url = base_url + "/salary/qrcode/validate/"

        qrcode_string = str(uuid.uuid4())
        vals["qrcode"] = url + qrcode_string
        vals["qrcode_string"] = qrcode_string

        res = super(HrEmployeeSalaryLetter, self).create(vals)
        return res


    def action_print(self):
        self.ensure_one()
        res = {}
        if not self.template_id:
            raise ValidationError(_('Sorry, You must select Template.'))
        mail_values = self.template_id.generate_email(self.id)
        self.body_html = mail_values.get('body_html',False)
        # record = self.env['hr.employee.salary.letter'].create({'body_html':mail_values.get('body_html',False),'end_service_id':self.end_service_id.id,'template_id':self.template_id.id})
        return self.action_print1()



    def action_print1(self):
        data= self.read()
        datas = {
            'ids': [],
            'model': 'hr.employee.salary.letter',
            'form': data
        }
        return self.env.ref('ejad_erp_hr.hr_employee_salary_letter_report2').report_action(self, data=datas)
        #return self.env['report'].get_action(self,'ejad_erp_hr.hr_salary_template_report_pdf', data=datas)


    def action_print_no_header(self):
        self.ensure_one()
        res = {}
        if not self.template_id:
            raise ValidationError(_('Sorry, You must select Template.'))
            mail_values = self.template_id.generate_email(self.end_service_id.id)
        record = self.env['hr.employee.salary.letter'].create({'body_html':mail_values.get('body_html',False),'end_service_id':self.end_service_id.id,'template_id':self.template_id.id})
        return record.action_print_no_header()


    def preview(self):
        self.ensure_one()
        res = {}
        if not self.template_id:
            raise ValidationError(_('Sorry, You must select Template.'))
            mail_values = self.template_id.generate_email(self.end_service_id.id)
        record = self.env['hr.employee.salary.letter'].create({'body_html':mail_values.get('body_html',False),'end_service_id':self.end_service_id.id,'template_id':self.template_id.id})
        #return record.action_print()
        return {
            'name': _('End Service Documents (This is removable)'),
            'type': 'ir.actions.act_window',
            'res_model': 'hr.employee.salary.letter',
            'view_mode': 'form',
            'res_id': record.id,
            'target': 'current',
           }
        #print " 88888888888   ",mail_values
        return res


class MailTemplate(models.Model):
    _inherit = "mail.template"

    @api.model
    def get_defaults_model(self):
        if self._context.get('salary_template',False):
            model_ids = self.env['ir.model'].search([('model','=','hr.employee.salary.letter')])
            return model_ids and model_ids[0].id or False
        else:
            return False

    name = fields.Char()
    model_id = fields.Many2one(default=get_defaults_model)



