# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import json


class QRCodeValidation(http.Controller):

    @http.route(["/salary/qrcode/validate/<string:qrcode_string>"], type="http", auth="none", website=True)
    def validate_salary_qrcode(self, qrcode_string=None):
        salary_template_id = request.env["hr.employee.salary.letter"].sudo().search([("qrcode_string", "=", qrcode_string)])
        salary_exist = False
        if salary_template_id:
            salary_exist = True
        return request.render(
            "ejad_erp_hr.validate_salary_qrcode", {"salary_template_id": salary_template_id,
                                                    "salary_exist": salary_exist}
        )

    @http.route(["/salary/qrcode/get_data/<string:qrcode_string>"], type="http", auth="none", website=True)
    def get_data(self, qrcode_string=None):
        salary_template_id = request.env["hr.employee.salary.letter"].sudo().search(
            [("qrcode_string", "=", qrcode_string)])
        if salary_template_id:
            return json.dumps(
                {"result": {'verified': 1,
                            'emp_name': salary_template_id[0].sudo().contract_id.employee_id.name,
                            'en_emp_name': salary_template_id[0].sudo().contract_id.employee_id.en_name,
                            'identification': salary_template_id[0].sudo().contract_id.employee_id.identification_id,
                            #'job': salary_template_id[0].sudo().contract_id.employee_id.job_id.name,
                            'date': salary_template_id[0].date,
                            }}, ensure_ascii=False, )
        else:
            return json.dumps(
                {"result": {'verified': 0,
                            }}, ensure_ascii=False, )