# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    entity_type = fields.Selection([('person', 'Person'), ('company', 'Company'), ('public_sector', 'Public Sector')], string='Entity Type', tracking=True)
    tax_reg_no = fields.Char(string="Tax registration No", tracking=True)
    commercial_reg_no = fields.Char(string="Commercial registration No", tracking=True)
    person_name = fields.Char(string="Applicant's Name", tracking=True)
    ticket_type_id = fields.Many2one('helpdesk.ticket.type', string="Type", tracking=True)
    description = fields.Html(tracking=True)
    partner_email = fields.Char(string='Customer Email', compute='_compute_partner_email', store=True, readonly=False, tracking=True)
    partner_id = fields.Many2one('res.partner', string='Customer', tracking=True)
    region = fields.Selection([('1', 'Al-Riyadh'),
                               ('2', 'AL-Qassim'),
                               ('3', 'Makkah Al-mokarramah'),
                               ('4', 'Almadinah almonawara'),
                               ('5', 'Hail'),
                               ('6', 'Al-Jouf'),
                               ('7', 'Tabuk'),
                               ('8', 'Northen Border'),
                               ('9', 'Aseer'),
                               ('10', 'Jazan'),
                               ('11', 'Najran'),
                               ('12', 'Al-Baha'),
                               ('13', 'Eastren Province'),
                               ], string='Region',tracking=True)