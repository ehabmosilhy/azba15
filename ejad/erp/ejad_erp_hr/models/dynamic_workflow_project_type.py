# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError, Warning
import xml.etree.cElementTree as ET


class DynamicWorkflowProjectType(models.Model):
    _name = "workflow.project.type"
    _description = "Workflow Project Type"
    _inherit = ['mail.thread']

    def get_default_stage_ids(self):
        return self.env["dynamic.workflow.stage"].search([])

    name = fields.Char(string="Name", required=True, tracking=True)
    code = fields.Char(string="Code", required=True, tracking=True)

    service_beneficiary_ids = fields.Many2many("dynamic.workflow.service.beneficiary", "service_beneficiary_project_type",
                                               "service_beneficiary_id", "project_type_id", string="أنواع المستثمرين")
    color = fields.Char(string="Color", tracking=True)

    stage_ids = fields.Many2many("dynamic.workflow.stage", "project_type_stage", "project_type_id", "stage_id")

    simple_workflow = fields.Boolean(string="Simple Workflow", default=True)
    dynamic_workflow_category_id = fields.Many2one("dynamic.workflow.category", required=True, tracking=True)
    name_field_ids = fields.Char(related="additional_field_ids.name", tracking=True)
    additional_field_ids = fields.Many2many("additional.field.by.project.type", string="Fields")

    active = fields.Boolean(string="مفعل", default=True)

    @api.model
    def create(self, values):
        # if self.simple_workflow:
        if values.get("stage_ids", False):
            stage_ids = values.get("stage_ids", False)[0][2]
            self.check_validate_stages(stage_ids)

        workflow_project_type = super(DynamicWorkflowProjectType, self).create(values)

        return workflow_project_type

    def write(self, values):

        if self.simple_workflow:
            if values.get("stage_ids", False):
                stage_ids = values.get("stage_ids", False)[0][2]
                self.check_validate_stages(stage_ids)

        res = super(DynamicWorkflowProjectType, self).write(values)

        return res

    def check_validate_stages(self, stage_ids):
        stage_obj = self.env["dynamic.workflow.stage"]
        first_stage_number = 0
        last_stage_number = 0
        success_stage_number = 0
        for stage in stage_obj.browse(stage_ids):
            if stage.is_success_type:
                success_stage_number += 1
            if stage.is_refuse_type:
                last_stage_number += 1
            if stage.is_first_type:
                first_stage_number += 1
        if first_stage_number > 1:
            raise ValidationError(_("You have many first stages"))
        if first_stage_number == 0:
            raise ValidationError(_("You have to put a stage of first"))
        if success_stage_number > 1:
            raise ValidationError(_("You have many success stages"))
        if success_stage_number == 0:
            raise ValidationError(_("You have to put a stage of success"))
        if last_stage_number > 1:
            raise ValidationError(_("You have many last stages"))
        if last_stage_number == 0:
            raise ValidationError(_("You have to put stage of refuse"))

    _sql_constraints = [("uniq_code", "unique(code)", _("Code already used"))]


class AdditionalFieldByProjectType(models.Model):
    _name = "additional.field.by.project.type"
    _description = "Additional Field by Project Type"

    name = fields.Char(string="Display name")
    additional_field_id = fields.Many2one(
        "ir.model.fields", string="Field", domain="[('model_id.model','=','dynamic.workflow')]"
    )
