# -*- coding: utf-8 -*-

from odoo import fields, models, api


class DynamicWorkflowServiceBeneficiary(models.Model):
    _name = "dynamic.workflow.service.beneficiary"
    _description = "Dynamic Workflow Service Beneficiary"
    _inherit = 'mail.thread'

    name = fields.Char(string="الإسم", required=True, tracking=True)
    code = fields.Char(string="الرمز", required=True, tracking=True)

    project_type_ids = fields.Many2many("workflow.project.type", "service_beneficiary_project_type",
                                            "project_type_id", "service_beneficiary_id", string="المشروع")