# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    personal_id = fields.Char(string="Personal ID")
    # make this field store=True to make filter of customer menu action=action_helpdesk_customer_ticket run
    # ticket_count = fields.Integer("Tickets", compute='_compute_ticket_count', store=True)
    # ticket_count_x = fields.Boolean(compute="compute_ticket_count_x")
    #
    # def compute_ticket_count_x(self):
    #     for rec in self:
    #         print("computed")
    #         # retrieve all children partners and prefetch 'parent_id' on them
    #         all_partners = self.with_context(active_test=False).search([('id', 'child_of', self.ids)])
    #         all_partners.read(['parent_id'])
    #
    #         # group tickets by partner, and account for each partner in self
    #         groups = self.env['helpdesk.ticket'].read_group(
    #             [('partner_id', 'in', all_partners.ids)],
    #             fields=['partner_id'], groupby=['partner_id'],
    #         )
    #         rec.ticket_count = 0
    #         for group in groups:
    #             partner = self.browse(group['partner_id'][0])
    #             while partner:
    #                 if partner in rec:
    #                     partner.ticket_count += group['partner_id_count']
    #                 partner = partner.parent_id
    #         rec.ticket_count_x = True
