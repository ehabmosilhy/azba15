# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class contractRefuseWizard(models.TransientModel):

    _name = "dynamic.workflow.contract.refuse.wizard"
    _description = "Dynamic Workflow Contract Refuse Wizard"

    refuse_reason = fields.Char(string="Reason", required=True)


    def refuse_reason_function(self):

        context = dict(self._context or {})
        active_id = context.get("active_id", False)

        contract_id = self.env["hr.contract"].search([("id", "=", active_id)])
        refuse_stage_id = contract_id.stage_ids.search([("is_refuse_type", "=", True), ("contract_state", "=", True)])

        contract_id.write(
            {
                "refuse_reason": self.refuse_reason,
                "refuse_stage": contract_id.stage_id.id,
                "stage_id": refuse_stage_id.id,
                "state": refuse_stage_id.contract_state,
                "rejected_by": self.env.uid,
            }
        )

        return {"type": "ir.actions.act_window_close"}

class endofserviceRefuseWizard(models.TransientModel):

    _name = "dynamic.workflow.endofservice.refuse.wizard"
    _description = "Dynamic Workflow Endofservice Refuse Wizard"

    refuse_reason = fields.Char(string="Reason", required=True)


    def refuse_reason_function(self):

        context = dict(self._context or {})
        active_id = context.get("active_id", False)

        endofservice_id = self.env["hr.end.service"].search([("id", "=", active_id)])
        refuse_stage_id = endofservice_id.stage_ids.search([("endofservice_state", "=", 'cancel')])

        endofservice_id.write(
            {
                "refuse_reason": self.refuse_reason,
                "refuse_stage": endofservice_id.stage_id.id,
                "stage_id": refuse_stage_id.id,
                "state": refuse_stage_id.endofservice_state,
                "rejected_by": self.env.uid,
            }
        )
        if endofservice_id.move_id:
            endofservice_id.move_id.journal_id.update_posted = True
            endofservice_id.move_id.button_cancel()
            endofservice_id.move_id.unlink()

        return {"type": "ir.actions.act_window_close"}

class promotionRefuseWizard(models.TransientModel):
    _name = "dynamic.workflow.promotion.refuse.wizard"
    _description = "Dynamic Workflow Promotion Refuse Wizard"

    refuse_reason = fields.Char(string="Reason", required=True)


    def refuse_reason_function(self):

        context = dict(self._context or {})
        active_id = context.get("active_id", False)

        promotion_id = self.env["employee.promotion"].search([("id", "=", active_id)])
        refuse_stage_id = promotion_id.stage_ids.search([("is_refuse_type", "=", True), ("promotion_state", "=", 'refuse')])

        promotion_id.write(
            {
                "refuse_reason": self.refuse_reason,
                "refuse_stage": promotion_id.stage_id.id,
                "stage_id": refuse_stage_id.id,
                "state": refuse_stage_id.promotion_state,
                "rejected_by": self.env.uid,
            }
        )

        return {"type": "ir.actions.act_window_close"}

class deductionsRefuseWizard(models.TransientModel):
    _name = "dynamic.workflow.deductions.refuse.wizard"
    _description = "Dynamic Workflow Deductions Refuse Wizard"

    refuse_reason = fields.Char(string="Reason", required=True)


    def refuse_reason_function(self):

        context = dict(self._context or {})
        active_id = context.get("active_id", False)

        deductions_id = self.env["hr.deductions"].search([("id", "=", active_id)])
        refuse_stage_id = deductions_id.stage_ids.search([("is_refuse_type", "=", True), ("deductions_state", "!=", False)])

        deductions_id.write(
            {
                "refuse_reason": self.refuse_reason,
                "refuse_stage": deductions_id.stage_id.id,
                "stage_id": refuse_stage_id.id,
                "state": refuse_stage_id.deductions_state,
                "rejected_by": self.env.uid,
            }
        )

        return {"type": "ir.actions.act_window_close"}

