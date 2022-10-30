# -*- coding: utf-8 -*-

from odoo import models, fields, api


class HelpdeskTeam(models.Model):
    _inherit = "helpdesk.team"

    contactus_team = fields.Boolean(string="ContactUs Team")
    team_change_to = fields.Boolean(default=False)

    @api.model
    def search(self, domain, offset=0, limit=None, order=None, count=False):
        if self.env.user.has_group('helpdesk.group_helpdesk_user') and self.env.context.get('from_backend',False) == True:
            domain += [('visibility_member_ids', 'in', self.env.user.id)]
        res = super(HelpdeskTeam, self).search(domain, offset=offset, limit=limit, order=order,count=count)
        return res