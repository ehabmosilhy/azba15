from odoo import models, api


class AccountEdiFormat(models.Model):
    _inherit = 'account.edi.format'

    def _l10n_sa_export_zatca_invoice(self, invoice, xml_content=None):
        if xml_content:
            # Use simple string replacement since we're dealing with XML as text
            import re
            
            # Find all invoice line IDs and replace them with sequential numbers
            counter = 1
            def replace_id(match):
                nonlocal counter
                result = f'<cbc:ID>{counter}</cbc:ID>'
                counter += 1
                return result
                
            # Replace IDs between <cac:InvoiceLine> tags
            pattern = r'(<cac:InvoiceLine>.*?<cbc:ID>)\d+(<\/cbc:ID>)'
            xml_content = re.sub(pattern, lambda m: m.group(1) + str(counter) + m.group(2), xml_content, flags=re.DOTALL)
            
        return super(AccountEdiFormat, self)._l10n_sa_export_zatca_invoice(invoice, xml_content)

