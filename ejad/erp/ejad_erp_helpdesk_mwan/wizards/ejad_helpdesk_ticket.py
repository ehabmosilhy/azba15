# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from lxml import etree
import json

class HelpdeskConvertTeam(models.TransientModel):
    _name = 'helpdesk.convert.team'
    _description = 'Convert Team'

    # Helpdesk Dynamic Domain For Stages
    @api.onchange('team_id')
    def _domain_team_id(self):
        return {'domain': {'stage_id': [('team_ids', 'in', self.team_id.id),('stage_change_to',  '=', True)]}}

    # All Helpdesk Team For Selected Value That Replaced
    def get_all_team(self):
        ticket_obj = self.env['helpdesk.ticket'].browse(self._context.get('active_id', False))

        team_contactus_id = self.env['helpdesk.team'].sudo().search([('contactus_team', '=', True)], limit=1)
        if ticket_obj and ticket_obj.team_id.id != team_contactus_id.id:
            all_teams = self.env['helpdesk.team'].sudo().search([('id', '=', team_contactus_id.id)])
        else:
            all_teams = self.env['helpdesk.team'].sudo().search([('id', '!=', ticket_obj.team_id.id),('team_change_to', '=', True)])

        print("All Tems Object is equal : ",all_teams)
        return [(team.id, team.name) for team in all_teams]

    # Helpdesk Dynamic Domain For Team
    @api.onchange('all_teams')
    def get_team_id(self):
        self.team_id = int(self.all_teams)
        return {'type': 'ir.actions.client', 'tag': 'reload'}

    #all_teams = fields.Many2one('helpdesk.team',string="Helpdesk Team")
    all_teams = fields.Selection(string="Helpdesk Team", selection=get_all_team)
    team_id = fields.Many2one("helpdesk.team", string="Helpdesk Team",compute="get_team_id")
    stage_id = fields.Many2one("helpdesk.stage",compute='compute_stage_id', string="Helpdesk stage")

    @api.depends('team_id')
    def compute_stage_id(self):
        team_id =self.env['helpdesk.ticket'].browse(self._context.get('active_id', False)).team_id
        for rec in self:
            stage_obj = self.env['helpdesk.stage'].sudo().search(
                [('team_ids', 'in', team_id.id), ('stage_change_to', '=', True)],limit=1)
            rec.stage_id = stage_obj.id
    # Function To Save The Replaced Team

    def action_convert_team(self):
        ticket_id = self.env['helpdesk.ticket'].browse(self._context.get('active_id', False))
        old_team = False
        old_status = False
        print(self.all_teams)
        if ticket_id:
            old_team = ticket_id.team_id.name
            old_status = ticket_id.stage_id.name
            ticket_id.sudo().write({'team_id': self.team_id.id, 'stage_id': self.stage_id.id})
            team_change_msg = _("Change Team from %s to %s and the status from %s to %s by user %s") % (
                old_team, self.team_id.name, old_status, self.stage_id.name, self.env.user.name)
            ticket_id.message_post(body=team_change_msg)
        self.clear_caches()
        return {'type': 'ir.actions.client','tag':'reload'}


class HelpdeskStageInh(models.Model):
    _inherit = 'helpdesk.stage'

    stage_change_to = fields.Boolean(default=False)
