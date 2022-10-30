# -*- coding: utf-8 -*-

from odoo import api, models, fields


class ContractDynamicWorkflowStagePreviousWizard(models.TransientModel):
    _name = "dynamic.workflow.contract.stage.previous.wizard"
    _description = "Dynamic Workflow Contract Stage Previous Wizard"

    contract_id = fields.Many2one("hr.contract", string="Contract")
    stage_id = fields.Many2one("dynamic.workflow.stage", string="Stage", required=True)
    return_reason = fields.Char(string="Reason", required=True)

    @api.onchange("contract_id")
    def onchange_request_id(self):
        self.ensure_one()
        previous_stage_ids = self.env.context.get("previous_stage_ids")
        if previous_stage_ids:
            return {
                "domain": {"stage_id": [("id", "in", previous_stage_ids)]},
                "value": {"stage_id": previous_stage_ids[-1]},
            }
        return {}

    
    def action_previous(self):
        self.ensure_one()
        vals = {
            "return_reason": self.return_reason,
            "returned_by": self.env.user.id,
            "is_returned": True
        }
        if self.stage_id in self.contract_id.stage_ids:
            vals["stage_id"] = self.stage_id.id
            vals["state"] = self.stage_id.contract_state
            if self.stage_id.secondary_stage_ids:
                vals["current_second_stage"] = self.stage_id.secondary_stage_ids[0].id
        if self.stage_id in self.contract_id.secondary_stage_ids:
            vals["current_second_stage"] = self.stage_id.id
        self.contract_id.write(vals)

        user_id = self.env.user
        # employee_obj = self.env["hr.employee"].sudo().search([("user_id", "=", user_id.id)])
        # employee_obj.write({'waiting_reply_requests': [(4, self.contract_id.id, 0)]})


class EndofserDynamicWorkflowStagePreviousWizard(models.TransientModel):
    _name = "dynamic.workflow.endofservice.stage.previous.wizard"
    _description = "Dynamic Workflow Endofservice Stage Previous Wizard"

    endofservice_id = fields.Many2one("hr.end.service", string="End of Service")
    stage_id = fields.Many2one("dynamic.workflow.stage", string="Stage", required=True)
    return_reason = fields.Char(string="Reason", required=True)

    @api.onchange("endofservice_id")
    def onchange_request_id(self):
        self.ensure_one()
        previous_stage_ids = self.env.context.get("previous_stage_ids")
        if previous_stage_ids:
            return {
                "domain": {"stage_id": [("id", "in", previous_stage_ids)]},
                "value": {"stage_id": previous_stage_ids[-1]},
            }
        return {}

    
    def action_previous(self):
        self.ensure_one()
        vals = {
            "return_reason": self.return_reason,
            "returned_by": self.env.user.id,
            "is_returned": True
        }
        if self.stage_id in self.endofservice_id.stage_ids:
            vals["stage_id"] = self.stage_id.id
            vals["state"] = self.stage_id.endofservice_state
            if self.stage_id.secondary_stage_ids:
                vals["current_second_stage"] = self.stage_id.secondary_stage_ids[0].id
        if self.stage_id in self.endofservice_id.secondary_stage_ids:
            vals["current_second_stage"] = self.stage_id.id
        self.endofservice_id.write(vals)

        # user_id = self.env.user
        # employee_obj = self.env["hr.employee"].sudo().search([("user_id", "=", user_id.id)])
        # employee_obj.write({'waiting_reply_requests': [(4, self.endofservice_id.id, 0)]})


class PromotionDynamicWorkflowStagePreviousWizard(models.TransientModel):
    _name = "dynamic.workflow.promotion.stage.previous.wizard"
    _description = "Dynamic Workflow Promotion Stage Previous Wizard"

    promotion_id = fields.Many2one("employee.promotion", string="Promotion")
    stage_id = fields.Many2one("dynamic.workflow.stage", string="Stage", required=True)
    return_reason = fields.Char(string="Reason", required=True)

    @api.onchange("promotion_id")
    def onchange_request_id(self):
        self.ensure_one()
        previous_stage_ids = self.env.context.get("previous_stage_ids")
        if previous_stage_ids:
            return {
                "domain": {"stage_id": [("id", "in", previous_stage_ids)]},
                "value": {"stage_id": previous_stage_ids[-1]},
            }
        return {}

    
    def action_previous(self):
        self.ensure_one()
        vals = {
            "return_reason": self.return_reason,
            "returned_by": self.env.user.id,
            "is_returned": True
        }
        if self.stage_id in self.promotion_id.stage_ids:
            vals["stage_id"] = self.stage_id.id
            vals["state"] = self.stage_id.promotion_state
            if self.stage_id.secondary_stage_ids:
                vals["current_second_stage"] = self.stage_id.secondary_stage_ids[0].id
        if self.stage_id in self.promotion_id.secondary_stage_ids:
            vals["current_second_stage"] = self.stage_id.id
        self.promotion_id.write(vals)

        user_id = self.env.user
        # employee_obj = self.env["hr.employee"].sudo().search([("user_id", "=", user_id.id)])
        # employee_obj.write({'waiting_reply_requests': [(4, self.promotion_id.id, 0)]})


class mandateDynamicWorkflowStagePreviousWizard(models.TransientModel):
    _name = "dynamic.workflow.mandate.stage.previous.wizard"
    _description = "Dynamic Workflow Mandate Stage Previous Wizard"

    mandate_id = fields.Many2one("hr.mandate.request", string="mandate")
    stage_id = fields.Many2one("dynamic.workflow.stage", string="Stage", required=True)
    return_reason = fields.Char(string="Reason", required=True)

    @api.onchange("mandate_id")
    def onchange_request_id(self):
        self.ensure_one()
        previous_stage_ids = self.env.context.get("previous_stage_ids")
        if previous_stage_ids:
            return {
                "domain": {"stage_id": [("id", "in", previous_stage_ids)]},
                "value": {"stage_id": previous_stage_ids[-1]},
            }
        return {}

    
    def action_previous(self):
        self.ensure_one()
        vals = {
            "return_reason": self.return_reason,
            "returned_by": self.env.user.id,
            "is_returned": True
        }
        if self.stage_id in self.mandate_id.stage_ids:
            vals["stage_id"] = self.stage_id.id
            vals["state"] = self.stage_id.mandate_state
            if self.stage_id.secondary_stage_ids:
                vals["current_second_stage"] = self.stage_id.secondary_stage_ids[0].id
        if self.stage_id in self.mandate_id.secondary_stage_ids:
            vals["current_second_stage"] = self.stage_id.id
        self.mandate_id.write(vals)

        user_id = self.env.user
        # employee_obj = self.env["hr.employee"].sudo().search([("user_id", "=", user_id.id)])
        # employee_obj.write({'waiting_reply_requests': [(4, self.mandate_id.id, 0)]})


class holidaysDynamicWorkflowStagePreviousWizard(models.TransientModel):
    _name = "dynamic.workflow.holidays.stage.previous.wizard"
    _description = "Dynamic Workflow Holidays Stage Previous Wizard"

    holidays_id = fields.Many2one("hr.leave", string="holidays")
    stage_id = fields.Many2one("dynamic.workflow.stage", string="Stage", required=True)
    return_reason = fields.Char(string="Reason", required=True)

    @api.onchange("holidays_id")
    def onchange_request_id(self):
        self.ensure_one()
        previous_stage_ids = self.env.context.get("previous_stage_ids")
        if previous_stage_ids:
            return {
                "domain": {"stage_id": [("id", "in", previous_stage_ids)]},
                "value": {"stage_id": previous_stage_ids[-1]},
            }
        return {}

    
    def action_previous(self):
        self.ensure_one()
        vals = {
            "return_reason": self.return_reason,
            "returned_by": self.env.user.id,
            "is_returned": True
        }
        if self.stage_id in self.holidays_id.stage_ids:
            vals["stage_id"] = self.stage_id.id
            vals["state"] = self.stage_id.holidays_state
            if self.stage_id.secondary_stage_ids:
                vals["current_second_stage"] = self.stage_id.secondary_stage_ids[0].id
        if self.stage_id in self.holidays_id.secondary_stage_ids:
            vals["current_second_stage"] = self.stage_id.id
        self.holidays_id.write(vals)

        user_id = self.env.user
        # employee_obj = self.env["hr.employee"].sudo().search([("user_id", "=", user_id.id)])
        # employee_obj.write({'waiting_reply_requests': [(4, self.holidays_id.id, 0)]})