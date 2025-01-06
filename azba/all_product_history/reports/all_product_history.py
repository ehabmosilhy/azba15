# Copyright 2019 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AllProductHistoryView(models.TransientModel):
    _name = "all.product.history.view"
    _description = "All Product History View"
    _order = "product_id"

    product_id = fields.Many2one(comodel_name="product.product")
    product_in = fields.Float()
    product_out = fields.Float()
    initial_balance = fields.Float()
    balance = fields.Float()
    total_value = fields.Float()


class AllProductHistoryReport(models.TransientModel):
    _name = "report.all.product.history"
    _description = "All Product History Report"

    # Filters fields, used for data computation
    date_from = fields.Date()
    date_to = fields.Date()
    product_ids = fields.Many2many(comodel_name="product.product")

    # Data fields, used to browse report data
    results = fields.Many2many(
        comodel_name="all.product.history.view",
        compute="_compute_results",
        help="Use compute fields, so there is nothing store in database",
    )

    def _compute_results(self):
        self.ensure_one()
        self.date_to = self.date_to or fields.Date.context_today(self)

        # Get all products if none selected
        products = self.product_ids
        if not products:
            products = self.env['product.product'].search([('type', '=', 'product')])

        query = """
            WITH movements AS (
                SELECT 
                    v.product_id,
                    COALESCE(SUM(CASE 
                        WHEN v.create_date::date < %s THEN v.quantity 
                        ELSE 0 
                    END), 0) as initial_balance,
                    COALESCE(SUM(CASE 
                        WHEN v.create_date::date BETWEEN %s AND %s AND v.quantity > 0 THEN v.quantity 
                        ELSE 0 
                    END), 0) as product_in,
                    COALESCE(ABS(SUM(CASE 
                        WHEN v.create_date::date BETWEEN %s AND %s AND v.quantity < 0 THEN v.quantity 
                        ELSE 0 
                    END)), 0) as product_out,
                    COALESCE(SUM(v.value), 0) as total_value
                FROM stock_valuation_layer v
                WHERE v.product_id in %s
                GROUP BY v.product_id
            )
            SELECT 
                product_id,
                initial_balance,
                product_in,
                product_out,
                initial_balance + product_in - product_out as balance,
                total_value
            FROM movements
            ORDER BY product_id
        """
        params = (
            self.date_from,
            self.date_from, self.date_to,
            self.date_from, self.date_to,
            tuple(products.ids),
        )
        
        self._cr.execute(query, params)
        all_product_history_results = self._cr.dictfetchall()
        ReportLine = self.env["all.product.history.view"]
        self.results = [ReportLine.new(line).id for line in all_product_history_results]

    def _get_initial(self, product_id):
        """Get the total quantity for a product"""
        if not product_id:
            return 0.0
        product_line = self.results.filtered(lambda l: l.product_id.id == product_id.id)
        if not product_line:
            return 0.0
        return product_line.initial_balance

    def print_report(self, report_type="qweb"):
        self.ensure_one()
        action = (
            report_type == "xlsx"
            and self.env.ref("all_product_history.action_all_product_history_xlsx")
            or self.env.ref("all_product_history.action_all_product_history_pdf")
        )
        return action.report_action(self, config=False)
