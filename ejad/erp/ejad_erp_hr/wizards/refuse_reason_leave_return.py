# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class LeaveReturnrefuseWizard(models.TransientModel):
    _name = "leave.refuse.return.wizard"

    refuse_message = fields.Text(string="Reason Message", required=True)

    def refuse_reason(self):
        self = self.sudo()
        context = dict(self._context or {})
        active_id = context.get("active_id", False)
        leave_id = self.env["hr.leave.return"].search([("id", "=", active_id)])
        leave_id.write({"state": 'refuse' ,"refuse_message": self.refuse_message})
        leave_id.activity_feedback(['mail.mail_activity_data_todo'],
                               feedback='تم اكمال المهمة بنجاح شكرا لك')
        return {"type": "ir.actions.act_window_close"}
