# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging

from odoo import models, _

from odoo.tools import html2plaintext, plaintext2html

_logger = logging.getLogger(__name__)


class MailThread(models.AbstractModel):
    _inherit = 'mail.thread'

    def _message_whatsapp(self, body, subtype_id=False, partner_ids=False, number_field=False,
                     whatsapp_numbers=None, whatsapp_pid_to_number=None, **kwargs):
        """ Main method to post a message on a record using SMS-based notification
        method.

        :param body: content of SMS;
        :param subtype_id: mail.message.subtype used in mail.message associated
          to the whatsapp notification process;
        :param partner_ids: if set is a record set of partners to notify;
        :param number_field: if set is a name of field to use on current record
          to compute a number to notify;
        :param whatsapp_numbers: see ``_notify_record_by_whatsapp``;
        :param whatsapp_pid_to_number: see ``_notify_record_by_whatsapp``;
        """
        self.ensure_one()
        whatsapp_pid_to_number = whatsapp_pid_to_number if whatsapp_pid_to_number is not None else {}

        if number_field or (partner_ids is False and whatsapp_numbers is None):
            info = self._whatsapp_get_recipients_info(force_field=number_field)[self.id]
            info_partner_ids = info['partner'].ids if info['partner'] else False
            info_number = info['sanitized'] if info['sanitized'] else info['number']
            if info_partner_ids and info_number:
                whatsapp_pid_to_number[info_partner_ids[0]] = info_number
            if info_partner_ids:
                partner_ids = info_partner_ids + (partner_ids or [])
            if not info_partner_ids:
                if info_number:
                    whatsapp_numbers = [info_number] + (whatsapp_numbers or [])
                    # will send a falsy notification allowing to fix it through SMS wizards
                elif not whatsapp_numbers:
                    whatsapp_numbers = [False]
        #print ('==whatsapp_numbers==',partner_ids,whatsapp_numbers)
        if subtype_id is False:
            subtype_id = self.env['ir.model.data']._xmlid_to_res_id('mail.mt_note')
        for partner in partner_ids:
            whatsapp = partner._formatting_mobile_number() or partner.whatsapp
            body = body.replace('_PARTNER_', partner.name).replace('_NAME_', self.name).replace('_TIME_', self.display_time).replace('_LOCATION_', self.location).replace('_TAGS_', ', '.join(self.categ_ids.mapped('name'))).replace('_DESCRIPTION_', self.description)
            message_data = {
                'method': 'sendMessage',
                'phone': whatsapp,
                'body': body,
                'link': self.videocall_location or '',
            }
            self.message_post(
                    whatsapp_data=message_data,
                    body=plaintext2html(html2plaintext(body)), partner_ids=partner.ids or [],  # TDE FIXME: temp fix otherwise crash mail_thread.py
                    message_type='whatsapp', subtype_id=subtype_id,
                    whatsapp_numbers=whatsapp_numbers, whatsapp_pid_to_number=whatsapp_pid_to_number,
                    **kwargs
                )
        return

    def _message_whatsapp_with_template(self, template=False, template_xmlid=False, template_fallback='', partner_ids=False, **kwargs):
        """ Shortcut method to perform a _message_sms with an sms.template.

        :param template: a valid sms.template record;
        :param template_xmlid: XML ID of an sms.template (if no template given);
        :param template_fallback: plaintext (jinja-enabled) in case template
          and template xml id are falsy (for example due to deleted data);
        """
        self.ensure_one()
        if not template and template_xmlid:
            template = self.env.ref(template_xmlid, raise_if_not_found=False)
        if template:
            body = template._render_field('body', self.ids, compute_lang=True)[self.id]
        else:
            body = self.env['whatsapp.template']._render_template(template_fallback, self._name, self.ids)[self.id]
        return self._message_whatsapp(body, partner_ids=partner_ids, **kwargs)

#     def _get_default_whatsapp_recipients(self):
#         """ This method will likely need to be overriden by inherited models.
#                :returns partners: recordset of res.partner
#         """
#         partners = self.env['res.partner']
#         if hasattr(self, 'partner_id'):
#             partners |= self.mapped('partner_id')
#         if hasattr(self, 'partner_ids'):
#             partners |= self.mapped('partner_ids')
#         return partners
# 
#     def message_post_send_whatsapp(self, whatsapp_message, numbers=None, partners=None, note_msg=None, log_error=False):
#         """ Send an SMS text message and post an internal note in the chatter if successfull
#             :param sms_message: plaintext message to send by sms
#             :param partners: the numbers to send to, if none are given it will take those
#                                 from partners or _get_default_sms_recipients
#             :param partners: the recipients partners, if none are given it will take those
#                                 from _get_default_sms_recipients, this argument
#                                 is ignored if numbers is defined
#             :param note_msg: message to log in the chatter, if none is given a default one
#                              containing the sms_message is logged
#         """
#         if not numbers:
#             if not partners:
#                 partners = self._get_default_whatsapp_recipients()
# 
#             # Collect numbers, we will consider the message to be sent if at least one number can be found
#             numbers = list(set([i.whatsapp for i in partners if i.whatsapp]))
#         if numbers:
#             try:
#                 self.env.user.company_id._send_whatsapp(numbers, whatsapp_message)
#                 mail_message = note_msg or _('Whatsapp message sent: %s') % whatsapp_message
# 
#             except InsufficientCreditError as e:
#                 if not log_error:
#                     raise e
#                 mail_message = _('Insufficient credit, unable to send Whatsapp message: %s') % whatsapp_message
#         else:
#             mail_message = _('No whatsapp number defined, unable to send SMS message: %s') % whatsapp_message
# 
#         for thread in self:
#             thread.message_post(body=mail_message)
#         return False
