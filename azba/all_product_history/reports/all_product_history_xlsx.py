# Copyright 2019 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import models

from odoo.addons.report_xlsx_helper.report.report_xlsx_format import (
    FORMATS,
    XLS_HEADERS,
)

_logger = logging.getLogger(__name__)


class ReportAllProductHistoryXlsx(models.AbstractModel):
    _name = "report.all_product_history.report_all_product_history_xlsx"
    _description = "All Product History XLSX"
    _inherit = "report.report_xlsx.abstract"

    def generate_xlsx_report(self, workbook, data, objects):
        self._define_formats(workbook)
        ws_params = self._get_ws_params(workbook, data, objects)
        ws_name = ws_params.get("ws_name")
        ws_name = self._check_ws_name(ws_name)
        ws = workbook.add_worksheet(ws_name)
        self._all_product_history_report(workbook, ws, ws_params, data, objects)

    def _get_report_values(self, docids, data=None):
        wizard_id = data["wizard_id"]
        report = self.env["report.all.product.history"].browse(wizard_id)
        report._compute_results()
        return {
            "doc_ids": docids,
            "doc_model": "all.product.history.wizard",
            "docs": report,
            "date_from": report.date_from,
            "date_to": report.date_to,
        }

    def _get_ws_params(self, wb, data, objects):
        filter_template = {
            "1_date_from": {
                "header": {"value": "Date from"},
                "data": {
                    "value": self._render("date_from"),
                    "format": FORMATS["format_tcell_date_center"],
                },
            },
            "2_date_to": {
                "header": {"value": "Date to"},
                "data": {
                    "value": self._render("date_to"),
                    "format": FORMATS["format_tcell_date_center"],
                },
            },
        }
        
        all_product_history_template = {
            "1_code": {
                "header": {"value": "Code"},
                "data": {
                    "value": self._render("code"),
                    "format": FORMATS["format_tcell_left"],
                },
                "width": 20,
            },
            "2_name": {
                "header": {"value": "Product"},
                "data": {
                    "value": self._render("name"),
                    "format": FORMATS["format_tcell_left"],
                },
                "width": 40,
            },
            "3_initial": {
                "header": {"value": "Initial Balance"},
                "data": {
                    "value": self._render("initial_balance"),
                    "format": FORMATS["format_tcell_amount_right"],
                },
                "width": 20,
            },
            "4_input": {
                "header": {"value": "Input"},
                "data": {
                    "value": self._render("input"),
                    "format": FORMATS["format_tcell_amount_right"],
                },
                "width": 20,
            },
            "5_output": {
                "header": {"value": "Output"},
                "data": {
                    "value": self._render("output"),
                    "format": FORMATS["format_tcell_amount_right"],
                },
                "width": 20,
            },
            "6_balance": {
                "header": {"value": "Final Balance"},
                "data": {
                    "value": self._render("balance"),
                    "format": FORMATS["format_tcell_amount_right"],
                },
                "width": 20,
            },
            "7_value": {
                "header": {"value": "Total Value"},
                "data": {
                    "value": self._render("value"),
                    "format": FORMATS["format_tcell_amount_right"],
                },
                "width": 20,
            },
        }

        ws_params = {
            "ws_name": "All Products History",
            "generate_ws_method": "_all_product_history_report",
            "title": "All Products History Report",
            "wanted_list_filter": [k for k in sorted(filter_template.keys())],
            "col_specs_filter": filter_template,
            "wanted_list": [k for k in sorted(all_product_history_template.keys())],
            "col_specs": all_product_history_template,
        }
        return ws_params

    def _all_product_history_report(self, wb, ws, ws_params, data, objects):
        ws.set_portrait()
        ws.fit_to_pages(1, 0)
        ws.set_header(XLS_HEADERS["xls_headers"]["standard"])
        ws.set_footer(XLS_HEADERS["xls_footers"]["standard"])

        self._set_column_width(ws, ws_params)

        row_pos = 0
        row_pos = self._write_ws_title(ws, row_pos, ws_params)

        # Write filters
        row_pos = self._write_line(
            ws,
            row_pos,
            ws_params,
            col_specs_section="header_filter",
            default_format=FORMATS["format_theader_blue_center"],
        )
        row_pos = self._write_line(
            ws,
            row_pos,
            ws_params,
            col_specs_section="data_filter",
            render_space={
                "date_from": objects.date_from or "",
                "date_to": objects.date_to or "",
            },
            default_format=FORMATS["format_tcell_date_center"],
        )

        row_pos += 1

        # Write table header
        row_pos = self._write_line(
            ws,
            row_pos,
            ws_params,
            col_specs_section="header",
            default_format=FORMATS["format_theader_blue_center"],
        )

        # Get products
        products = objects.product_ids or objects.env["product.product"].search([("type", "=", "product")])
        
        # Write product lines
        for product in products:
            product_line = objects.results.filtered(lambda l: l.product_id == product)
            if product_line:
                row_pos = self._write_line(
                    ws,
                    row_pos,
                    ws_params,
                    col_specs_section="data",
                    render_space={
                        "code": product.product_tmpl_id.code.strip() or "",
                        "name": product.name,
                        "initial_balance": product_line.initial_balance,
                        "input": product_line.product_in,
                        "output": product_line.product_out,
                        "balance": product_line.balance,
                        "value": product_line.total_value,
                    },
                    default_format=FORMATS["format_tcell_amount_right"],
                )
            else:
                row_pos = self._write_line(
                    ws,
                    row_pos,
                    ws_params,
                    col_specs_section="data",
                    render_space={
                        "code": product.product_tmpl_id.code.strip() or "",
                        "name": product.name,
                        "initial_balance": 0,
                        "input": 0,
                        "output": 0,
                        "balance": 0,
                        "value": 0,
                    },
                    default_format=FORMATS["format_tcell_amount_right"],
                )
