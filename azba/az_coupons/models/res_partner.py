# See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _, sql_db
from odoo.exceptions import UserError, ValidationError
import requests
import json
import re
import time
import logging

_logger = logging.getLogger(__name__)


class Partner(models.Model):
    _inherit = "res.partner"
    
    whatsapp_number = fields.Char('Whatsapp Number')
