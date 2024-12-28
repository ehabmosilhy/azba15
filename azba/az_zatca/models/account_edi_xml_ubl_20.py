from odoo import models, api
from lxml import etree
from odoo.tools.xml_utils import cleanup_xml_node


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