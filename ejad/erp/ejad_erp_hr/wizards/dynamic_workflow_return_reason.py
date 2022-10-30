# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class EndofserviceReturnWizard(models.TransientModel):
    _name = "dynamic.workflowendofservice.return.wizard"
    _description = "Dynamic Workflowendofservice Return Wizard"

    return_message = fields.Text(string="Reason Message", required=True)

    
    def return_reason(self):

        context = dict(self._context or {})
        active_id = context.get("active_id", False)
        request_id = self.env["hr.end.service"].sudo().search([("id", "=", active_id)])

        return_message = "<b>Return message</b><br/>" + self.return_message
        # search and go to the first stage
        first_stage = request_id.stage_ids.search([("is_first_type", "=", True)])

        request_id.write({"stage_id": first_stage.id,
                          "return_message": self.return_message,
                          "is_returned": True})

        return {"type": "ir.actions.act_window_close"}

class deductionsReturnWizard(models.TransientModel):
    _name = "dynamic.workflow.deductions.return.wizard"
    _description = "Dynamic Workflow Deductions Return Wizard"

    return_message = fields.Text(string="Reason Message", required=True)

    
    def return_reason(self):

        context = dict(self._context or {})
        active_id = context.get("active_id", False)
        request_id = self.env["hr.deductions"].sudo().search([("id", "=", active_id)])

        return_message = "<b>Return message</b><br/>" + self.return_message
        # search and go to the first stage
        first_stage = request_id.stage_ids.search([("is_first_type", "=", True)])

        request_id.write({"stage_id": first_stage.id,
                          "return_message": self.return_message,
                          "is_returned": True})

        return {"type": "ir.actions.act_window_close"}

class mandateReturnWizard(models.TransientModel):
    _name = "dynamic.workflow.mandate.return.wizard"
    _description = "Dynamic Workflow Mandate Return Wizard"

    return_message = fields.Text(string="Reason Message", required=True)

    
    def return_reason(self):

        context = dict(self._context or {})
        active_id = context.get("active_id", False)
        request_id = self.env["hr.mandate.request"].sudo().search([("id", "=", active_id)])

        return_message = "<b>Return message</b><br/>" + self.return_message
        # search and go to the first stage
        first_stage = request_id.stage_ids.search([("is_first_type", "=", True)])

        request_id.write({"stage_id": first_stage.id,
                          "return_message": self.return_message,
                          "is_returned": True})

        return {"type": "ir.actions.act_window_close"}

