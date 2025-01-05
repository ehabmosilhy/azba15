# Copyright 2019 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AllProductHistoryView(models.TransientModel):
    _name = "all.product.history.view"
    _description = "All Product History View"
    _order = "date"

    date = fields.Datetime()
    product_id = fields.Many2one(comodel_name="product.product")
    product_qty = fields.Float()
    product_uom_qty = fields.Float()
    product_uom = fields.Many2one(comodel_name="uom.uom")
    reference = fields.Char()
    location_id = fields.Many2one(comodel_name="stock.location")
    location_dest_id = fields.Many2one(comodel_name="stock.location")
    is_initial = fields.Boolean()
    product_in = fields.Float()
    product_out = fields.Float()
    picking_id = fields.Many2one(comodel_name="stock.picking")

    def name_get(self):
        result = []
        for rec in self:
            name = rec.reference
            if rec.picking_id.origin:
                name = "{} ({})".format(name, rec.picking_id.origin)
            result.append((rec.id, name))
        return result


class AllProductHistoryReport(models.TransientModel):
    _name = "report.all.product.history"
    _description = "All Product History Report"

    # Filters fields, used for data computation
    date_from = fields.Date()
    date_to = fields.Date()
    product_ids = fields.Many2many(comodel_name="product.product")
    location_id = fields.Many2one(comodel_name="stock.location")

    # Data fields, used to browse report data
    results = fields.Many2many(
        comodel_name="all.product.history.view",
        compute="_compute_results",
        help="Use compute fields, so there is nothing store in database",
    )

    def _compute_results(self):
        self.ensure_one()
        date_from = self.date_from or "0001-01-01"
        self.date_to = self.date_to or fields.Date.context_today(self)
        # locations = self.env["stock.location"].search(
        #     [("id", "child_of", [self.location_id.id])]
        # )
        locations = self.env["stock.location"].search(
            []
        )

        query = """
            SELECT move.date, move.product_id, move.product_qty,
                move.product_uom_qty, move.product_uom, move.reference,
                move.location_id, move.location_dest_id,
                case when move.location_dest_id in %s
                    then move.product_qty end as product_in,
                case when move.location_id in %s
                    then move.product_qty end as product_out,
                case when move.date < %s then True else False end as is_initial,
                move.picking_id
            FROM stock_move move
            WHERE (move.location_id in %s or move.location_dest_id in %s)
                and move.state = 'done' and move.product_id in %s
                and CAST(move.date AS date) <= %s
            ORDER BY move.date, move.reference
        """
        params = (
            tuple(locations.ids),
            tuple(locations.ids),
            date_from,
            tuple(locations.ids),
            tuple(locations.ids),
            tuple(self.product_ids.ids),
            self.date_to,
        )
        
        # Combine query and parameters for debugging
        debug_query = self._cr.mogrify(query, params).decode('utf-8')
        
        self._cr.execute(query, params)
        all_product_history_results = self._cr.dictfetchall()
        ReportLine = self.env["all.product.history.view"]
        self.results = [ReportLine.new(line).id for line in all_product_history_results]

    def _get_initial(self, product_line):
        product_input_qty = sum(product_line.mapped("product_in"))
        product_output_qty = sum(product_line.mapped("product_out"))
        return product_input_qty - product_output_qty

    def print_report(self, report_type="qweb"):
        self.ensure_one()
        action = (
            report_type == "xlsx"
            and self.env.ref("all_product_history.action_all_product_history_xlsx")
            or self.env.ref("all_product_history.action_all_product_history_pdf")
        )
        return action.report_action(self, config=False)
