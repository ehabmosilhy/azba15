from odoo import apix, SUPERUSER_ID

def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    invoices_to_update = env['account.move'].search([('invoice_origin', '=', False), ('batch_purchase_id', '!=', False)])
    for invoice in invoices_to_update:
        invoice.write({'invoice_origin': invoice.batch_purchase_id})
