from odoo import http
import json


class UpdateController(http.Controller):

    @http.route('/api/update', auth='public', csrf=False, methods=['POST', 'GET'])
    def update(self, **kwargs):
        data = http.request.httprequest.data
        data=data.decode("utf-8", "ignore")
        return f"Thank you very much, we have received the following data\n {data}"
