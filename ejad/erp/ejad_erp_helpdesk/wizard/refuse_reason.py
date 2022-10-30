# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class HelpdeskfuseWizard(models.TransientModel):
    _name = "helpdesk.refuse.wizard"
    _description = "refuse Wizard"

    refuse_message = fields.Text(string="Reason Message", required=True)

    def refuse_reason(self):
        self = self.sudo()
        context = dict(self._context or {})
        active_id = context.get("active_id", False)
        obj_data = self.env["helpdesk.ticket"].search([("id", "=", active_id)])

        refuse_message = "<b>Refuse message</b><br/>" + self.refuse_message
        stage_id = self.env['helpdesk.stage'].search(
            [('is_refused', '=', True), ('team_ids', 'in', [obj_data.team_id.id])], limit=1).id

        obj_data.write({"stage_id": stage_id,"refuse_message": self.refuse_message})
        obj_data.activity_feedback(['mail.mail_activity_data_todo'], feedback='تم اكمال المهمة بنجاح شكرا لك')
        return {"type": "ir.actions.act_window_close"}
