from odoo import fields, models, api



import time

from odoo.http import Response
import os

from odoo.service.server import PreforkServer, memory_info
from odoo.http import JsonRequest
from odoo import http
from odoo import tools

import logging
import socket
import os
import signal
import sys

import odoo
from odoo.tools import config

_logger = logging.getLogger(__name__)


class Monitor(models.Model):
    _name = "tools.monitor"
    def log_data(self):
        _logger.info(f":::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::")
        _logger.info(f":::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::")
        _logger.info(f":::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::")
        _logger.info(f":::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::")
        _logger.info(f":::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::")
        r=Response
        _logger.info(f"******* Ehab -> User{self.env.user.login}")

        _logger.info(f":::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::")
        _logger.info(f":::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::")
        _logger.info(f":::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::")
        _logger.info(f":::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::")
        _logger.info(f":::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::")


