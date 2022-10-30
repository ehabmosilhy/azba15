# -*- coding: utf-8 -*-

import logging
from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class EmployeeMandateType(models.Model):
    _name = 'hr.mandate.type'
    _description = 'Employee Mandate Type'

    name = fields.Char('Name')
    type = fields.Selection([
        ('internal', 'Internal'),
        ('external', 'External'),
    ], string='Mandate Type', required=True)
    saudi_cities_ids = fields.One2many('saudi.city', 'mandate_type_id', 'Saudi Arabia Cities')
    countries_ids = fields.One2many('res.country', 'mandate_type_id', 'Other Countries')
    number_days = fields.Integer('Mandate Days')
    number_days_before = fields.Integer('Days Before Mandate')
    number_days_after = fields.Integer('Days After Mandate')
    account_id = fields.Many2one('account.account', string='Mandate Account')


class SaudiCities(models.Model):
    _name = 'saudi.city'
    _description = 'Saudi Cities'

    name = fields.Char('City Name')
    mandate_type_id = fields.Many2one('hr.mandate.type', string="Mandate Type", ondelete="set null")


class ResCountry(models.Model):
    _name = 'res.country'
    _description = 'Res Country'
    _inherit = ['res.country']

    mandate_type_id = fields.Many2one('hr.mandate.type', string="Mandate Type", ondelete="set null")


class MandateReason(models.Model):
    _name = 'mandate.reason'
    _description = 'Mandates Reasons'
    _order = 'name'

    name = fields.Char('Type')


class MandateAmount(models.Model):
    _name = 'mandate.amount'
    _description = 'Mandates Amount'

    name = fields.Char('Name')
    internal_amount = fields.Float('مبلغ الإنتداب الداخلي')
    external_amount = fields.Float('مبلغ الإنتداب الخارجي')
    job_ids = fields.One2many('hr.job', 'mandate_amount_conf_id', 'الوظائف')


class HRJob(models.Model):
    _name = 'hr.job'
    _inherit = ['hr.job']

    mandate_amount_conf_id = fields.Many2one('mandate.amount', string="إعداد مبلغ الأنتداب", ondelete="set null")
