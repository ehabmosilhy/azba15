from markupsafe import Markup
from odoo import _, fields, models, api
from odoo.exceptions import UserError
from odoo.addons.account.models.account_move import AccountMove as BaseAccountMove

class AccountMove(models.Model):
    _inherit = 'account.move'

    def _post(self, soft=True):
        # OVERRIDE
        # Call the base account.move implementation directly to bypass account_edi
        posted = BaseAccountMove._post(self, soft=soft)
        
        edi_document_vals_list = []
        for move in posted:
            for edi_format in move.journal_id.edi_format_ids:
                # ZATCA E-Invoicing Control Block
                # ================================
                # Purpose: Control when ZATCA e-invoicing should be processed
                # Because MultiCompany is not handled well in original Odoo Zatca Modules
                # We need to enable ZATCA API in some companies but not in others
                # Check if ZATCA API is enabled in company settings
                zatca_api_needed = move.company_id.l10n_sa_api_mode
                
                # Determine if EDI processing is needed based on 3 conditions:
                # 1. ZATCA API mode is enabled (zatca_api_needed)
                # 2. Document is an invoice (is_invoice)
                # 3. EDI format is required for this invoice (_is_required_for_invoice)
                is_edi_needed = zatca_api_needed and move.is_invoice(include_receipts=False) and edi_format._is_required_for_invoice(move)
                # ================================
                
                if is_edi_needed:
                    errors = edi_format._check_move_configuration(move)
                    if errors:
                        raise UserError(_("Invalid invoice configuration:\n\n%s") % '\n'.join(errors))

                    existing_edi_document = move.edi_document_ids.filtered(lambda x: x.edi_format_id == edi_format)
                    if existing_edi_document:
                        existing_edi_document.write({
                            'state': 'to_send',
                            'attachment_id': False,
                        })
                    else:
                        edi_document_vals_list.append({
                            'edi_format_id': edi_format.id,
                            'move_id': move.id,
                            'state': 'to_send',
                        })

        if edi_document_vals_list:
            self.env['account.edi.document'].create(edi_document_vals_list)
            posted.edi_document_ids._process_documents_no_web_services()
            self.env.ref('account_edi.ir_cron_edi_network')._trigger()
        
        return posted
