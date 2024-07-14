# -*- coding: utf-8 -*-
import logging

import requests
import json
import base64
from odoo import api, fields, models, _, sql_db, tools
from odoo.tools.mimetypes import guess_mimetype
from odoo.exceptions import AccessError, UserError, ValidationError

import html2text
from odoo.addons.aos_whatsapp.klikapi import texttohtml
from ..klikapi import KlikApi
#from odoo.addons.aos_whatsapp.klikapi import KlikApi
_logger = logging.getLogger(__name__)


class POSOrder(models.Model):
    _inherit = 'pos.order'

    def _get_default_whatsapp_recipients(self):
        return []
    
    def _formatting_mobile_number(self, rec, whatsapp):
        module_rec = self.env['ir.module.module'].sudo().search_count([
            ('name', '=', 'crm_phone_validation'),
            ('state', '=', 'installed')])
        country_code = str(rec.country_id.phone_code) if rec.country_id else str(self.company_id.country_id.phone_code)
        country_count = len(str(rec.country_id.phone_code))
        whatsapp_number = rec.whatsapp
        if rec.whatsapp[:country_count] == str(rec.country_id.phone_code):
            whatsapp_number = rec.whatsapp
        elif rec.whatsapp[0] == '0':
            if rec.whatsapp[1:country_count+1] == str(rec.country_id.phone_code):
                #COUNTRY CODE UDH DIDEPAN
                whatsapp_number = rec.whatsapp[1:]
            else:
                whatsapp_number = country_code + rec.whatsapp[1:]
        return whatsapp_number
        # return module_rec and re.sub("[^0-9]", '', whatsapp) or \
        #     str(partner.country_id.phone_code) + whatsapp[1:] if whatsapp[0] == '0' else whatsapp

    def _formatting_mobile_number_country(self, country_id, whatsapp):
        module_rec = self.env['ir.module.module'].sudo().search_count([
            ('name', '=', 'crm_phone_validation'),
            ('state', '=', 'installed')])
        
        country = self.env['res.country'].browse(country_id)
        country_code = str(country.phone_code) if country else str(self.env.user.company_id.country_id.phone_code)
        country_count = len(str(country.phone_code))
        whatsapp_number = whatsapp
        if whatsapp[:country_count] == str(country.phone_code):
            whatsapp_number = whatsapp
        elif whatsapp[0] == '0':
            if whatsapp[1:country_count+1] == str(country.phone_code):
                #COUNTRY CODE UDH DIDEPAN
                whatsapp_number = whatsapp[1:]
            else:
                whatsapp_number = country_code + whatsapp[1:]
        return whatsapp_number
    # def _get_whatsapp_server(self):
    #     WhatsappServer = self.env['ir.whatsapp_server']
    #     whatsapp_ids = WhatsappServer.search([('status','=','authenticated')], order='sequence asc')
    #     if len(whatsapp_ids) == 1:
    #         return whatsapp_ids
    #     return False
    
    # def klikapi(self):
    #     self.ensure_one()
    #     was = self.config_id._get_whatsapp_server()
    #     return KlikApi(was.klik_key, was.klik_secret)
    
    # def _get_mail_message_whatsapp(self):
    #     for was in self:
    #         KlikApi = was.klikapi()
    #         KlikApi.auth()
    #         was.message_counts = KlikApi.get_count()
    #         was.message_response = KlikApi.get_limit()

    def klikapi(self):
        #self.ensure_one()
        was = self.config_id.whatsapp_server_id
        #print ('==klikapi==',was,was.klik_key, was.klik_secret)
        return KlikApi(was.klik_key, was.klik_secret)
    
    # def _get_mail_message_whatsapp(self):
    #     for was in self:
    #         KlikApi = was.klikapi()
    #         KlikApi.auth()
    #         was.message_counts = KlikApi.get_count()
    #         was.message_response = KlikApi.get_limit()

    def klikapi_config(self, config):
        WhatsappServer = self.env['ir.whatsapp_server']
        whatsapp_ids = WhatsappServer.search([('id','=',config.get('whatsapp_server_id')[0]),('status','=','authenticated')], order='sequence asc')
        return KlikApi(whatsapp_ids.klik_key, whatsapp_ids.klik_secret)

    def get_number_exist(self, config, order, value):
        #URL http://wa.klikodoo.id/checknumber?number=6281288776713&check=6282333808291@s.whatsapp.net
        #WhatsappServer = self.env['ir.whatsapp_server']
        #whatsapp_ids = WhatsappServer.browse(config.get('whatsapp_server_id')[0])
        #whatsapp_ids = WhatsappServer.search([('id','=',config.get('whatsapp_server_id')[0]),('status','=','authenticated')], order='sequence asc')
        #if whatsapp_ids:
        #    KlikApi(whatsapp_ids.klik_key, whatsapp_ids.klik_secret)
        KlikApi = self.klikapi_config(config)
        KlikApi.auth()
        # whatsapp = self._formatting_mobile_number(partner, client['whatsapp'])
        data = {'number': self._formatting_mobile_number_country(order['client'].get('country_id')[0], value)}
        #print ('===KlikApi==',)
        response = KlikApi.get_number(data)
        print ('==response==',self,order['client'].get('country_id')[0],response['exists'])
        return True
            
    def _prepare_mail_message(self, author_id, chat_id, record, model, body, data, subject, partner_ids, attachment_ids, response, status):
        values = {
            'author_id': author_id,
            'model': model or 'res.partner',
            'res_id': record,#model and self.ids[0] or False,
            'body': body,
            'whatsapp_data': data,
            'subject': subject or False,
            'message_type': 'whatsapp',
            'record_name': subject,
            'partner_ids': [(4, pid) for pid in partner_ids],
            'attachment_ids': attachment_ids and [(6, 0, attachment_ids.ids)],
            'whatsapp_method': data['method'],
            'whatsapp_chat_id': chat_id,
            'whatsapp_response': response,
            'whatsapp_status': status,
        }
        return values
    
    def action_whatsapp_to_customer(self, name, client, ticket):
        if not self:
            return False
        if not client.get('whatsapp'):
            return False
        new_cr = sql_db.db_connect(self.env.cr.dbname).cursor()
        message = client['message']
        MailMessage = self.env['mail.message']
        get_version = self.env["ir.module.module"].sudo().search([('name','=','base')], limit=1).latest_version
        #message = _("Dear *%s*, Here is your electronic ticket for the %s.") % (client['name'], name)
        #print ('===message===',name, client, message)
        #ticket = self._context.get('receipt_data')
        #if self._get_whatsapp_server() and self._get_whatsapp_server().status == 'authenticated':
        if self.config_id.whatsapp_server_id and self.config_id.whatsapp_server_id.status == 'authenticated':
            #if whatsapp_server.status == 'authenticated':
            #print ('===message===',self._get_whatsapp_server().status)
            KlikApi = self.config_id.whatsapp_server_id.klikapi()   
            KlikApi.auth()   
            attachment_ids = []
            chatIDs = []
            message_data = {}
            send_message = {}
            status = 'error'
            #partners = self.env['res.partner'].browse(client['id'])
            # if client['id']:
            #     partners = client['id']
                # if client['order'].partner_id.child_ids:
                #     #ADDED CHILD FROM PARTNER
                #     for partner in client['order'].partner_id.child_ids:
                #         partners += partner
            filename = 'Receipt-' + name + '.jpg'
            attachment = self.env['ir.attachment'].search([('store_fname','=',filename)])
            #print ('==attachment=11=',attachment)
            if not attachment:
                attachment = self.env['ir.attachment'].create({
                    'name': filename,
                    'type': 'binary',
                    'datas': ticket,
                    'res_model': 'pos.order',
                    'res_id': self.ids[0],
                    'store_fname': filename,
                    'mimetype': 'image/jpeg',
                })
            message_attach = {
                'method': 'sendFile',
                #'phone': whatsapp,
                'body': 'data:image/jpeg;base64,' + str(attachment.datas.decode("utf-8")),
                'filename': filename,
                'caption': message,#att['filename'],
                'get_version': get_version,
            }
            if client['whatsapp']:
                print ('no-customer--',client)
                whatsapp = client['whatsapp']
                message_attach.update({'phone': whatsapp})
                data_attach = json.dumps(message_attach)
                send_attach = KlikApi.post_request(method='sendFile', data=data_attach)
                #print ('==attachment=33=',send_attach)
                if send_attach.get('message')['sent']:
                    status = 'send'
                    _logger.warning('Success to send Message to WhatsApp number %s', client['whatsapp'])
                else:
                    status = 'error'
                    _logger.warning('Failed to send Message to WhatsApp number %s', client['whatsapp'])
                chatID = None
                vals = self._prepare_mail_message(self.env.user.partner_id.id, chatID, self.id, 'pos.order', texttohtml.formatHtml(message.replace('\xa0', ' ')), message_attach, name, [], [], send_attach, status)
                MailMessage.sudo().create(vals)
                new_cr.commit()
            # if client['order']['client']:
            #     print ('with-customer--',client)
            #     partner = self.env['res.partner'].browse(client['order']['client']['id'])
            #     if (client['whatsapp'] or partner.whatsapp):
            #         #SEND MESSAGE
            #         whatsapp = self._formatting_mobile_number(partner, client['whatsapp'])
            #         message_attach.update({'phone': whatsapp})
            #         data_attach = json.dumps(message_attach)
            #         #print ('==attachment=33=',data_attach)
            #         send_attach = KlikApi.post_request(method='sendFile', data=data_attach)
            #         #print ('==attachment=33=',send_attach)
            #         if send_attach.get('message')['sent']:
            #             partner.whatsapp = client['whatsapp']
            #             status = 'send'
            #             _logger.warning('Success to send Message to WhatsApp number %s', whatsapp)
            #         else:
            #             status = 'error'
            #             _logger.warning('Failed to send Message to WhatsApp number %s', whatsapp)
            #         chatID = None
            #         vals = self._prepare_mail_message(self.env.user.partner_id.id, chatID, self.id, 'pos.order', texttohtml.formatHtml(message.replace('_PARTNER_', self.partner_id.name).replace('\xa0', ' ')), message_attach, name, [partner.id], [], send_attach, status)
            #         MailMessage.sudo().create(vals)
            #         new_cr.commit()
        else:
            _logger.error('Could not sent whatsapp the POS Order')
            #results = False
        return
