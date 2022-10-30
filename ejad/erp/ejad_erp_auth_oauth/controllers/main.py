# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging

import json

import werkzeug.urls
import werkzeug.utils

from odoo.http import request
from odoo.addons.auth_oauth.controllers.main import OAuthLogin as Home
from odoo.addons.web.controllers.main import Home as Homeweb
from odoo import api, http, SUPERUSER_ID, _
from passlib.context import CryptContext
import pyotp
import datetime as dt
import requests as req
import re
from odoo.exceptions import AccessDenied
from odoo.addons.auth_oauth.controllers.main import OAuthController
_logger = logging.getLogger(__name__)

#----------------------------------------------------------
# Controller
#----------------------------------------------------------
class HomeWeb(Homeweb):

    @http.route('/web', type='http', auth="none")
    def web_client(self, s_action=None, **kw):
        res = super(HomeWeb, self).web_client(s_action=s_action, **kw)
        otp_signin_auth = request.env['ir.default'].sudo().get('res.config.settings', 'signin_auth')
        if otp_signin_auth and request.env.user.mobile and not request.session.get('otp_auth_success',
                                                                                                  False):
            return werkzeug.utils.redirect('/web/login', 303)
        return res

    @http.route()
    def web_login(self, redirect=None, *args, **kw):
        res = super(HomeWeb, self).web_login(redirect=redirect, *args, **kw)
        otp_signin_auth = request.env['ir.default'].sudo().get('res.config.settings', 'signin_auth')
        if request.params['login_success'] and otp_signin_auth and request.env.user.mobile and not request.session.get(
                'otp_auth_success', False):
            return request.redirect('/web/login/totp')
        return res


class OAuthControllerProvider(OAuthController):

    @http.route('/auth_oauth/signin', type='http', auth='none')
    def signin(self, **kw):
        res = super(OAuthControllerProvider, self).signin(**kw)
        if kw['session_state']:
            return request.redirect('/web/login/totp')
        return res
class OAuthLogin(Home):

    #

    @http.route('/web/login/totp', type='http', auth='public', methods=['GET', 'POST'], sitemap=False, website=True)
    def web_totp(self, redirect=None, **kwargs):
        if not request.session.uid:
            return request.redirect('/web/login')

        user = request.env['res.users'].browse(request.session.uid)
        totp = request.session.get('otploginobj')
        otp_time = request.session.get('otp_time')
        if user.mobile and not totp:
            otp_time = request.env['ir.default'].sudo().get('res.config.settings', 'otp_time_limit')
            otp_time = int(otp_time)
            base32Code = pyotp.random_base32()
            totp = pyotp.TOTP(base32Code, interval=otp_time)
            request.session['otploginobj'] = totp
            code = totp.now()
            txt = "رمز التفعيل : {}".format(code)
            # TODO SET ALL PARAMETER IN VIEW NOT CODE
            url = "https://apis.deewan.sa/sms/v1/messages"
            payload = {
                "senderName": "MWAN",
                "messageType": "text",
                "flashing": 0,
                "messageText": txt,
                "recipients": user.mobile,
            }
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbiI6IjAyY2I2NDAxNWJmM2U4MGQzZGU4NGYwMTUyMWNjMmIxNDJlNDJjOTc1YTc4MmViYTYxNGQ2ODM4ZjJiZmE1ZGY1NzIyYjhlNDY0MTVkNzU0ZGExZjdjYzM1MGI0YzIwYmFkNDY1NTI2ZDEwODZiYTA1ZGYyNDI1OGY2NzM5YjBkNGQ4ZDQyMWFkMGI1OTE2ZDI3NzE1NTE4YjZlZWZmNTIiLCJpYXQiOjE2NDU2MTQwNzAsImV4cCI6MzIyMzQ5NDA3MH0.eTtnbYGGGH9YEQ-oZoFfmfO8kRZp0U_AEFSPm8r3I70"
            }
            response = req.request("POST", url, json=payload, headers=headers)
            start = dt.datetime.now()
            end = dt.datetime.now()
            rest = (end - start).total_seconds()
            if rest < otp_time:
                otp_time = int(otp_time - rest)
                request.session['otp_time'] = otp_time
        error = None
        if request.httprequest.method == 'POST':
            user = request.env['res.users'].browse(request.session.uid)
            totp = request.session.get('otploginobj')
            verify = totp.verify(kwargs.get('totp_token'))
            if verify:
                return request.redirect(self._login_redirect(request.session.uid, redirect=redirect))
            else:
                error = _("رمز التثبت خاطئ ..")
                return request.render('ejad_erp_auth_oauth.totp_template', {
                    'error': error,
                    'redirect': redirect,
                    'otpTimeLimit':otp_time,
                    'userid': user.id,
                })
        if user.mobile:
            return request.render('ejad_erp_auth_oauth.totp_template', {
                'error': error,
                'redirect': redirect,
                'otpTimeLimit': otp_time,
                'userid':user.id,
            })
        else:
            return request.redirect(self._login_redirect(request.session.uid, redirect=redirect))


    @http.route(['/check/mobile'], type='json', auth="public", methods=['POST'], website=True)
    def check_user_mobile(self, login=''):
        message = []
        signin_auth = request.env['ir.default'].sudo().get('res.config.settings', 'signin_auth')
        auth = signin_auth and 1 or -1
        if login:
            user = request.env["res.users"].sudo().search([
                '|',
                '|',
                ("mobile", "=", login),
                ("login", "=", login),
                ("email", "=", login)]
            )
            if user:
                is_mobile = user.partner_id.mobile
                if is_mobile:
                    message = ['mobile', _("حساب برقم جوال"), auth]
                else:
                    message = ['not mobile', _("حساب من غير رقم جوال"), auth]
        return message

    @http.route(['/verify/sms'], type='json', auth="public", methods=['POST'], website=True)
    def verify_sms(self, sms_code=''):
        if sms_code:
            totp = request.session.get('otploginobj')
            verify = totp.verify(sms_code)

            if verify:
                request.session['otp_auth_success'] = True
                message = [5, _("رمز التحقق صحيح .."), 0]
            else:
                request.session['otp_auth_success'] = False
                message = [7, _("رمز التحقق خاطئ ..")]
        else:
            request.session['otp_auth_success'] = False
            message = [7, _("الرجاء إدخال رمز التحقق ..")]
        return message

    @http.route(['/send/sms'], type='json', auth="public", methods=['POST'], website=True)
    def send_sms(self, userid=''):

        if userid:
            user = request.env["res.users"].sudo().search([("id", "=", int(userid))]
            )
            if user and user.mobile:
                otp_time = request.env['ir.default'].sudo().get('res.config.settings', 'otp_time_limit')
                otp_time = int(otp_time)
                base32Code = pyotp.random_base32()
                totp = pyotp.TOTP(base32Code, interval=otp_time)
                request.session['otploginobj'] = totp
                code = totp.now()
                txt = "رمز التفعيل : {}".format(code)
                # TODO SET ALL PARAMETER IN VIEW NOT CODE
                url = "https://apis.deewan.sa/sms/v1/messages"

                payload = {
                    "senderName": "MWAN",
                    "messageType": "text",
                    "flashing": 0,
                    "messageText": txt,
                    "recipients": user.mobile,
                }
                headers = {
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                    "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbiI6IjAyY2I2NDAxNWJmM2U4MGQzZGU4NGYwMTUyMWNjMmIxNDJlNDJjOTc1YTc4MmViYTYxNGQ2ODM4ZjJiZmE1ZGY1NzIyYjhlNDY0MTVkNzU0ZGExZjdjYzM1MGI0YzIwYmFkNDY1NTI2ZDEwODZiYTA1ZGYyNDI1OGY2NzM5YjBkNGQ4ZDQyMWFkMGI1OTE2ZDI3NzE1NTE4YjZlZWZmNTIiLCJpYXQiOjE2NDU2MTQwNzAsImV4cCI6MzIyMzQ5NDA3MH0.eTtnbYGGGH9YEQ-oZoFfmfO8kRZp0U_AEFSPm8r3I70"
                }

                response = req.request("POST", url, json=payload, headers=headers)
                start = dt.datetime.now()

                # username = 'Hamza@mewa.gov.sa'
                # password = 'S9V$I$KAgs'
                # number = user.mobile
                # sender = 'MEWA'
                #
                # response = req.get(
                #     "https://xservices.rich.sa/RiCHClientServiceREST.svc/SendSmsLoginGet?username={0}&password={1}&Sender={2}&Text={3}&number={4}".format(
                #         username, password, sender, txt, number))
                end = dt.datetime.now()
                rest = (end - start).total_seconds()
                if rest < otp_time:
                    otp_time = int(otp_time - rest)
                message = [2, _("Good password .."), otp_time]
            else:
                message = [0, _("الرجاء التأكد من أن المعرف صحيح .."), 0]
        else:
            message = [0, _("الرجاء إدخال معرف .."), 0]

        return message


    def list_providers(self):
        try:
            providers = request.env['auth.oauth.provider'].sudo().search_read([('enabled', '=', True)])
        except Exception:
            providers = []
        for provider in providers:
            # request.httprequest.url_root
            auth_oauth_url = request.env['ir.config_parameter'].sudo().get_param('ejad_erp_auth_oauth.return_url')
            if auth_oauth_url:
                return_url = auth_oauth_url + 'auth_oauth/signin'
            else:
                return_url = request.httprequest.url_root + 'auth_oauth/signin'
            state = self.get_state(provider)
            params = dict(
                response_type=provider['response_type'],
                client_id=provider['client_id'],
                redirect_uri=return_url,
                scope=provider['scope'],
                state=json.dumps(state),
            )
            # provider['auth_link'] = "%s?%s" % (provider['auth_endpoint'], werkzeug.url_encode(params))
            provider['auth_link'] = "%s?%s" % (provider['auth_endpoint'], werkzeug.urls.url_encode(params))
        return providers