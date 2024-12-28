from odoo import models, api
from lxml import etree
from odoo.tools.xml_utils import cleanup_xml_node


class AccountEdiFormat(models.Model):
    _inherit = 'account.edi.format'

    # def _l10n_sa_export_zatca_invoice(self, invoice, xml_content=None):
    #     """
    #     Export invoice to ZATCA (Saudi Arabia E-Invoicing) format while ensuring invoice line IDs comply with
    #     the 6-digit limitation requirement.
        
    #     This method modifies the XML content to replace potentially large invoice line IDs with sequential
    #     numbers, as ZATCA system rejects invoice line IDs that exceed 6 digits.
        
    #     :param invoice: The invoice record to be exported
    #     :param xml_content: The XML content to be modified (if provided)
    #     :return: The processed XML content with compliant invoice line IDs
    #     """
    #     if xml_content:
    #         # Use simple string replacement since we're dealing with XML as text
    #         import re
            
    #         # Find all invoice line IDs and replace them with sequential numbers
    #         counter = 1
    #         def replace_id(match):
    #             nonlocal counter
    #             result = f'<cbc:ID>{counter}</cbc:ID>'
    #             counter += 1
    #             return result
                
    #         # Replace IDs between <cac:InvoiceLine> tags
    #         pattern = r'(<cac:InvoiceLine>.*?<cbc:ID>)\d+(<\/cbc:ID>)'
    #         xml_content = re.sub(pattern, lambda m: m.group(1) + str(counter) + m.group(2), xml_content, flags=re.DOTALL)
            
    #     return super(AccountEdiFormat, self)._l10n_sa_export_zatca_invoice(invoice, xml_content)


class AccountEdiXmlUBL20(models.AbstractModel):
    _inherit = "account.edi.xml.ubl_20"
    
    def _handle_invoice_line_ids(self, vals):
        """
        Modify invoice line IDs in the vals structure to use sequential numbers.
        
        :param vals: Dictionary containing invoice data
        :return: Modified dictionary with sequential invoice line IDs
        """
        if 'vals' in vals and 'invoice_line_vals' in vals['vals']:
            for index, line in enumerate(vals['vals']['invoice_line_vals'], start=1):
                line['id'] = str(index)
        return vals

    def _export_invoice(self, invoice):
        """
        Export invoice with modified invoice line IDs to comply with requirements.
        This method ensures invoice line IDs are properly formatted before export.
        
        :param invoice: The invoice record to be exported
        :return: Tuple containing XML content and any validation errors
        """
        vals = self._export_invoice_vals(invoice)
        vals = self._handle_invoice_line_ids(vals)
        
        errors = [constraint for constraint in self._export_invoice_constraints(invoice, vals).values() if constraint]
        xml_content = self.env['ir.qweb']._render(vals['main_template'], vals)
        xml_content = b"<?xml version='1.0' encoding='UTF-8'?>\n" + etree.tostring(cleanup_xml_node(xml_content))
        return xml_content, set(errors)