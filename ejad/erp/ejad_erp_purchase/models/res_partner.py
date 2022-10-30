# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from datetime import datetime, date



class ResUSer(models.Model):

    _inherit = 'res.users'
    is_user_purchase_representative = fields.Boolean('هل هو مندوب مشتريات')

class ResPartner(models.Model):

    _inherit = 'res.partner'

    @api.depends('comm_reg_expiry','social_insurance_reg_expiry','chamber_reg_expiry','zakat_reg_expiry','saudi_reg_expiry')
    def _compute_expired_files(self):
        date_now = date.today()

        for rec in self:
            if rec.comm_reg_expiry:
                if rec.comm_reg_expiry < date_now :
                    rec.expired_files += 1

            if rec.social_insurance_reg_expiry:
                if rec.social_insurance_reg_expiry < date_now :
                    rec.expired_files += 1

            if rec.chamber_reg_expiry:
                if rec.chamber_reg_expiry < date_now :
                    rec.expired_files += 1

            if rec.zakat_reg_expiry:
                if rec.zakat_reg_expiry < date_now :
                    rec.expired_files += 1

            if rec.saudi_reg_expiry:
                if rec.saudi_reg_expiry < date_now :
                    rec.expired_files += 1

    commercial_reg = fields.Char('السجل التجاري')
    comm_reg_expiry = fields.Date('تاريخ الإنتهاء')
    commercial_attachment_id = fields.Binary(string="وثيقة السجل التجاري", track_visibility='onchange')
    commercial_filename = fields.Char()

    social_insurance_reg = fields.Char('التامينات الاجتماعية')
    social_insurance_reg_expiry = fields.Date('تاريخ الإنتهاء')
    social_insurance_attachment_id = fields.Binary(string="وثيقة التامينات الاجتماعية", track_visibility='onchange')
    social_filename = fields.Char()

    chamber_reg = fields.Char('الغرفة التجارية')
    chamber_reg_expiry = fields.Date('تاريخ الإنتهاء')
    chamber_attachment_id = fields.Binary(string="وثيقة الغرفة التجارية", track_visibility='onchange')
    chamber_filename = fields.Char()

    zakat_reg = fields.Char('شهادة الزكاة و الدخل')
    zakat_reg_expiry = fields.Date('تاريخ الإنتهاء')
    zakat_attachment_id = fields.Binary(string="وثيقة الزكاة", track_visibility='onchange')
    zakat_filename = fields.Char()

    saudi_reg = fields.Char('شهادة السعودة')
    saudi_reg_expiry = fields.Date('تاريخ الإنتهاء')
    saudi_attachment_id = fields.Binary(string="شهادة السعودة", track_visibility='onchange')
    saudi_filename = fields.Char()

    expired_files = fields.Integer(compute='_compute_expired_files', string="وثايق منتهية الصلحية", store=True, )

    
    def send_mail_expired_files(self):
        """ Open a window to compose an email, with the edi invoice template
            message loaded by default
        """
        self.ensure_one()

        template = self.env.ref('ejad_erp_purchase.nauss_mail_template', False)
        compose_form = self.env.ref('mail.email_compose_message_wizard_form', False)
        ctx = dict(
            default_model='res.partner',
            default_res_id=self.id,
            default_use_template=bool(template),
            default_template_id=template and template.id or False,
            default_composition_mode='comment',
            #mark_invoice_as_sent=True,
            #custom_layout="account.mail_template_data_notification_email_account_invoice",
            force_email=True
        )
        return {
            'name': _('Compose Email'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form.id, 'form')],
            'view_id': compose_form.id,
            'target': 'new',
            'context': ctx,
        }