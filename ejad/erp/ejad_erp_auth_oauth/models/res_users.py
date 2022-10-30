# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import json
import logging
import requests
from odoo.http import request
from odoo import api, fields, models
from odoo.exceptions import AccessDenied, UserError
from odoo.addons.auth_signup.models.res_users import SignupError

from odoo.addons import base
base.models.res_users.USER_PRIVATE_FIELDS.append('oauth_access_token')

_logger = logging.getLogger(__name__)

try:
    import jwt
except ImportError:
    _logger.warning("The PyJWT python library is not installed, login with Microsoft OAuth2 won't be available.")
    jwt = None


class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.model
    def _auth_oauth_code_validate(self, provider, code):
        """ requests access_token using provided code and returns
        the validation data corresponding to the access token
        """
        auth_oauth_url = self.env['ir.config_parameter'].sudo().get_param('ejad_erp_auth_oauth.return_url')
        if auth_oauth_url:
            return_url = auth_oauth_url + 'auth_oauth/signin'
        else:
            return_url = request.httprequest.url_root + 'auth_oauth/signin'

        oauth_provider = self.env['auth.oauth.provider'].browse(provider)
        req_params = dict(
            client_id=oauth_provider.client_id,
            client_secret=oauth_provider.client_secret,
            grant_type='authorization_code',
            code=code,
            redirect_uri= return_url ,
        )

        headers = {'Accept': 'application/json'}
        token_info = requests.post(oauth_provider.validation_endpoint, headers=headers, data=req_params).json()
        _logger.info("====== The Token Info Is ===== %s", token_info)
        if token_info.get("error"):
           raise Exception(token_info['error'])

        access_token = token_info.get('access_token')
        validation = {
            'access_token': access_token
        }

        if token_info.get('id_token'):
            # Used in case of Microsoft's Azure AD API
            # We can directly access basic info from 'id_token', without
            # making another call to any data_endpoint

            if not jwt:
                _logger.warning("The PyJWT python library is missing, not able to login with Microsoft Account.")
                raise AccessDenied()

            data = jwt.decode(token_info['id_token'], 'secret', algorithms=['HS256'],options={"verify_signature": False},verify=False)

        else:
            # For other providers, fetch data using data_endpoint
            data = self._auth_oauth_rpc(oauth_provider.data_endpoint, access_token)

        validation.update(data)

        return validation

    @api.model
    def auth_oauth(self, provider, params):
        # Advice by Google (to avoid Confused Deputy Problem)
        # if validation.audience != OUR_CLIENT_ID:
        #   abort()
        # else:
        #   continue with the process
        if params.get('code'):
            # code grant flow, which will give code to retrieve access_token
            validation = self._auth_oauth_code_validate(provider, params['code'])
            access_token = validation.pop('access_token')
            params['access_token'] = access_token
        else:
            # implicit flow, which directly gives access_token
            access_token = params.get('access_token')
            validation = self._auth_oauth_validate(provider, access_token)

        # required check
        if not validation.get('user_id'):
            # Workaround for Facebook and Microsoft as they do not send 'user_id'
            if validation.get('id'):  # for Facebook
                validation['user_id'] = validation['id']

            elif validation.get('oid'):  # for Microsoft
                validation['user_id'] = validation['oid']
            else:
                raise AccessDenied()

        # retrieve and sign in user
        login = self._auth_oauth_signin(provider, validation, params)
        if not login:
            raise AccessDenied()
        # return user credentials
        return (self.env.cr.dbname, login, access_token)
