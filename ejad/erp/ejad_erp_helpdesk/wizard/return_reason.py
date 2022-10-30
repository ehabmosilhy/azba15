# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class HelpdeskturnWizard(models.TransientModel):
    _name = "helpdesk.return.wizard"
    _description = "Return Wizard"

    return_message = fields.Text(string="Reason Message", required=True)

    def return_reason(self):
        context = dict(self._context or {})
        active_id = context.get("active_id", False)
        obj_data = self.env["helpdesk.ticket"].search([("id", "=", active_id)])

        return_message = "<b>Return message</b><br/>" + self.return_message

        obj_data.action_return()
        obj_data.write({"return_message": self.return_message, "is_returned": True})

        return {"type": "ir.actions.act_window_close"}

