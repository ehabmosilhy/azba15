import uuid
import json
from markupsafe import Markup
from odoo import _, fields, models, api
from odoo.tools import float_repr
from datetime import datetime
from base64 import b64decode, b64encode
from lxml import etree
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from cryptography.hazmat.backends import default_backend
from cryptography.x509 import load_der_x509_certificate


class AccountMove(models.Model):
    _inherit = 'account.move'

    zatca_response_log = fields.Html(string='ZATCA Response Log', readonly=True, copy=False,
                                   help='Full log of the latest ZATCA response')

    def _l10n_sa_log_results(self, xml_content, response_data=None, error=False):
        """
            Save submitted invoice XML hash in case of either Rejection or Acceptance.
        """
        self.ensure_one()
        self.journal_id.l10n_sa_latest_submission_hash = self.env['account.edi.xml.ubl_21.zatca']._l10n_sa_generate_invoice_xml_hash(
            xml_content)
            
        bootstrap_cls, title, content = ("success", _("Invoice Successfully Submitted to ZATCA"),
                                         "" if (not error or not response_data) else response_data)
        if error:
            bootstrap_cls, title = ("danger", _("Invoice was rejected by ZATCA"))
            content = Markup("""
                <p class='mb-0'>
                    %s
                </p>
                <hr>
                <p class='mb-0'>
                    %s
                </p>
            """) % (_('The invoice was rejected by ZATCA. Please, check the response below:'), response_data)
        if response_data and response_data.get('validationResults', {}).get('warningMessages'):
            bootstrap_cls, title = ("warning", _("Invoice was Accepted by ZATCA (with Warnings)"))
            content = Markup("""
                <p class='mb-0'>
                    %s
                </p>
                <hr>
                <p class='mb-0'>
                    %s
                </p>
            """) % (_('The invoice was accepted by ZATCA, but returned warnings. Please, check the response below:'), "<br/>".join([Markup("<b>%s</b> : %s") % (m['code'], m['message']) for m in response_data['validationResults']['warningMessages']]))
        
        self.zatca_response_log = Markup("""
            <div role='alert' class='alert alert-%s'>
                <h4 class='alert-heading'>%s</h4>%s
            </div>
        """) % (bootstrap_cls, title, content)