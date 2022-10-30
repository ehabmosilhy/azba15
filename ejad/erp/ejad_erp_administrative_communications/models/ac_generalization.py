# -*- encoding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime
# from ummalqura.hijri_date import HijriDate


class AdministrativeCommunicationsGeneralization(models.Model):
    _name = "ac.generalization"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "التعميمات"
    _order = "id desc"

    def hijri_day_name(self, date):
        # if date:
        #     hijri_date = HijriDate(int(date[:4]), int(date[5:7]), int(date[8:10]), gr=True)
        #     return hijri_date.day_name
        # else:
        return False

    def hijri_date(self, date):
        # if date:
        #     dd = str(HijriDate.get_hijri_date(str(date[:10])))
        #     new_dd = dd[8:10] + "/" + dd[5:7] + "/" + dd[0:4]
        #     return new_dd
        # else:
        return False

    dest = fields.Selection([
        ('dept', 'إدارة/ قسم'),
        ('emp', 'موظف'),
        ('beneficiary', 'مستفيد'),
        ('auditor', 'مراجع')], string='الجهة الطالبة للتصدير', tracking=True)
    partner_id = fields.Many2one('res.partner', string='المستفيد', tracking=True)
    employee_id = fields.Many2one('hr.employee', string='الموظف', tracking=True)
    country_id = fields.Many2one('res.country', string='الدولة', tracking=True)
    # odoo 13
    # department_id4 = fields.Many2one('hr.department', string='إدارة/ قسم', tracking=True)
    ident_no = fields.Char('رقم بطاقة الهوية', tracking=True)
    auditor = fields.Char('المراجع', tracking=True)
    name = fields.Char(string='الإسم', readonly=False)
    subject = fields.Char(string="الموضوع", required=True)
    details = fields.Text('نص الموضوع')
    date = fields.Datetime(string="التاريخ", default=fields.Datetime.now)
    scope = fields.Selection([
        ('global', 'عام'),
        ('departments', 'اختيار إداراة')
    ], string="النطاق", required=True, tracking=True)
    type1 = fields.Selection([
        ('t', 'قرار'),
        ('g', 'تعميم')
    ], string="النوع", required=True, tracking=True, default="t")
    state = fields.Selection([
        ('draft', 'مسودة'),
        ('sent', 'مرسلة'),
        ('canceled', 'ملغاة')
    ], default='draft', tracking=True)
    department_ids = fields.Many2many("hr.department", string="الإدارات المعنيّة")
    attachment_ids = fields.One2many(comodel_name="ac.generalization.attachment", inverse_name="generalization_id",
                                     string="المرفقات")
    attachments_no = fields.Integer('عدد المشفوعات')
    operation_ids = fields.One2many(comodel_name="ac.operation", inverse_name="generalization_id", string="المعاملات")
    department_sequence = fields.Char(string='كود الادارة/القسم', tracking=True, )

    @api.model
    def create(self, vals):
        #vals.update({'name': self.env['ir.sequence'].next_by_code('ac.operation.generalization')})
        res = super(AdministrativeCommunicationsGeneralization, self).create(vals)
        res.name = self.env['ir.sequence'].next_by_code('ac.operation.generalization')
        print('  ########  ', res)
        return res


    @api.constrains('scope', 'department_ids')
    def _check_departments(self):
        if self.scope == 'departments' and not self.department_ids:
            raise UserError(_("لا بد من تعيين إدارة على الأقل !"))

    
    def action_open_operation(self):

        ctx = self._context.copy()
        action_rec = self.env['ir.model.data'].xmlid_to_object('ejad_erp_administrative_communications.action_ac_operation_in')

        action = action_rec.read([])[0]
        action['context'] = ctx
        action['domain'] = [('generalization_id', '=', self.id)]
        return action

    
    def action_send(self):
        self.ensure_one()

        list_departments = (self.scope == 'global') and self.env['hr.department'].search([('is_ac_eligible', '=', True)]) or self.department_ids
        host = self.env.user.company_id.host or 'localhost:8069'
        action_id = self.env.ref('ejad_erp_administrative_communications.action_ac_operation_in').id

        for department in list_departments:
            for employee in department.member_ids:

                operation_data = {
                    'subject': self.subject + ' --> إلى الموظف: ' + employee.name,
                    'details': self.details,
                    'type_op': 'internal',
                    'type': 'generalization',
                    'nature': self.env.ref('ejad_erp_administrative_communications.operation_nature_generalization').id,
                    'generalization_id': self.id,
                    'state': 'done',
                    'is_employee_inbox': True,
                    'state_detailed': 'employee_inbox',
                    'name': self.env['ir.sequence'].next_by_code('ac.operation.internal')
                     }
                operation_id = self.env['ac.operation'].create(operation_data)
                operation_id.write({'assigned_employee_id': employee.id})
                operation_id.write({'is_employee_outbox': False})
                self._cr.execute("delete from mail_followers where res_model = 'ac.operation' and res_id =%d" % operation_id.id)

                if employee.user_id:

                    reg = {
                        'res_id': operation_id.id,
                        'res_model': 'ac.operation',
                        'partner_id': employee.user_id.partner_id.id
                    }

                    self.env['mail.followers'].create(reg)

                    msg_data = {'subject': 'تعميم',
                                'date': datetime.today(),
                                'body': 'لقد تم إحالة هذه المعاملة : ' +
                                        '<a href="http://' + host +
                                        '/web#id=' + str(operation_id.id) +
                                        '&view_type=form&action=' +
                                        str(action_id) + '&model=ac.operation">' + self.subject + '</a>' +
                                        ' إليكم و هي عبارة عن تعميم .! ',
                                'message_type': 'notification'
                    }
                    msg_id = self.env['mail.message'].create(msg_data)

                    notif_data = {
                        'mail_message_id': msg_id.id,
                        'res_partner_id': employee.user_id.partner_id.id,
                        'is_read': False,
                        'notification_type': 'email'
                    }
                    self.env['mail.notification'].create(notif_data)

        self.state = 'sent'

        return {
            'effect': {
                'fadeout': 'slow',
                'message': 'لقد تم إرسال التعميم بنجاح ',
                'img_url': '/ejad_erp_administrative_communications/static/src/img/loading.gif',
                'type': 'rainbow_man',
            }
        }

    
    def action_cancel(self):
        self.state = 'canceled'


class ACGeneralizationAttachments(models.Model):
    _name = "ac.generalization.attachment"
    _description = "Ac Generalization Attachment"

    name = fields.Char(string='اسم المرفق', required=True)
    attachment_id = fields.Binary(string="المرفق", required=True)
    attachment_filename = fields.Char()
    generalization_id = fields.Many2one(comodel_name="ac.generalization")
