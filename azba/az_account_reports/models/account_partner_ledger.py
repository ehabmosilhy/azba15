# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from markupsafe import Markup
from odoo import models, api, _
from odoo.tools import config
from lxml import etree, html
import base64


class ReportPartnerLedger(models.AbstractModel):
    _inherit = "account.partner.ledger"

    def _get_columns_name(self, options):
        if self.env.context.get('print_mode'):
            columns = [
                {},
                # {'name': _('JRNL')},
                # {'name': _('Account')},
                {'name': _('Ref')},
                # {'name': _('Due Date'), 'class': 'date'},
                # {'name': _('Matching Number')},
                {'name': _('Initial Balance'), 'class': 'number'},
                {'name': _('Debit'), 'class': 'number'},
                {'name': _('Credit'), 'class': 'number'}]

            if self.user_has_groups('base.group_multi_currency'):
                columns.append({'name': _('Amount Currency'), 'class': 'number'})

            columns.append({'name': _('Balance'), 'class': 'number'})

            return columns
        else:
            return super(ReportPartnerLedger, self)._get_columns_name(options)

    @api.model
    def _get_lines(self, options, line_id=None):
        if self.env.context.get('print_mode'):
            offset = int(options.get('lines_offset', 0))
            remaining = int(options.get('lines_remaining', 0))
            balance_progress = float(options.get('lines_progress', 0))

            if offset > 0:
                # Case a line is expanded using the load more.
                lml = self._load_more_lines(options, line_id, offset, remaining, balance_progress)
                return lml
            else:
                # Case the whole report is loaded or a line is expanded for the first time.
                pll = self._get_partner_ledger_lines(options, line_id=line_id)

                '''
                To Remove
    
                    options['headers'][0][2] {'name': 'Account'}
                    options['headers'][0][5] {'name': 'Matching Number'}
                    
                    
                    pll[n]['columns'][1] 'Account'
                    pll[n]['columns'][4] 'Matching Number'
                    
                To Change:
                    pll[0]['colspan'] -> Reduce by 2
                    pll[-1]['colspan'] -> Reduce by 2
    
                '''
                if options.get('headers'):
                    options['headers'][0].pop(1)  # Jrnl
                    options['headers'][0].pop(1)  # Account
                    options['headers'][0].pop(2)  # Due Date
                    options['headers'][0].pop(2)  # Matching Number
                    # options['headers'][0].pop(2)  # Due Initial Balance

                    # pll[0]['colspan']-=2
                    # pll[-1]['colspan']-=2
                    for i in range(len(pll)):
                        if pll[i].get('colspan'):
                            # pll[i]['columns'].pop(0)  # Initial Balance
                            pll[i]['colspan'] -= 4
                        else:
                            pll[i]['columns'].pop(0)
                            pll[i]['columns'].pop(0)
                            pll[i]['columns'].pop(1)
                            pll[i]['columns'].pop(1)
                            # pll[i]['columns'].pop(1)

                            # حذف الرقم المرجعى للفاتورة من رقم الإشارة
                            splitted = pll[i]['columns'][0]['name'].split("-")
                            if splitted:
                                if len(splitted) > 2:
                                    if splitted[1].strip() == splitted[2].strip():
                                        splitted.pop(1)
                                        splitted.pop(1)
                                    else:
                                        splitted.pop(1)
                                elif len(splitted) == 2:
                                    splitted.pop(1)
                                pll[i]['columns'][0]['name'] = '-'.join(splitted)
                self.add_partner_codes(options)
                return pll
        else:
            return super(ReportPartnerLedger, self)._get_lines(options, line_id=None)

    def add_partner_codes(self, options):
        partner_codes = [self.env['res.partner'].search([('id', '=', _id)]).code for _id in options['partner_ids']]
        s = []
        for i in range(len(partner_codes)):
            s.append(options['selected_partner_ids'][i] + f"[{partner_codes[i]}]")
        options['selected_partner_ids'] = '-'.join(s)

    @api.model
    def _get_report_name(self):
        return 'Partner Ledger كشف حساب عميل'


def handle_body(self, body, options):
    date_from = options.get('date').get('date_from')
    date_to = options.get('date').get('date_to')

    logo = self.env['ir.attachment'].sudo().search([('name', '=', 'logo'),('company_id','=',  self.env.company.id)])
    logo_tag = f"""
    <img src='data:image/png;base64,{logo.datas.decode()}' alt='Company Logo' style='width: 250px;'>
    """ if logo else ""

    body_str = str(body)
    body_str = body_str.replace("SR", "").replace("آجل", "")

    # Parse the HTML
    root = html.fromstring(body_str)

    amount_elements = root.xpath("//*[contains(@class, 'o_account_report_column_value')]")

    # Get the last element
    last_element = amount_elements[-1] if amount_elements else None
    # If the last element exists, get its text content
    amount = last_element.text_content().replace(",", "").strip() if last_element is not None else 0
    status = "مدين" if float(amount) > 0 else "دائن"

    currency_record = self.env.user.company_id.currency_id
    amount = currency_record.amount_to_text(float(amount))

    amount = amount.replace('Riyal', 'ريال ').replace('Halala', 'هللة')

    body_str = body_str.replace("</body>", f"""
    <div style="direction:rtl;text-align:center;font-weight:bold;margin-bottom:10px;">
     رصيدكم لدينا 
    {amount}
    
     [{status}]
   
    </div>
     <footer style="text-align:center; font-size: large;width:90%;margin: auto;border:1px solid black;">
            نوافق على صحة الرصيد أعلاه .. وإذا لم نستلم منكم أى اعتراض على صحة هذا الكشف خلال أسبوع من تاريخه يعتبر الحساب صحيحاً ما عدا السهو والخطأ
        </footer>
        </body>
    """)

    root = html.fromstring(body_str)
    # Find the element you want to replace
    header_div_element = root.find('.//div[@class="o_account_reports_header"]')

    # Your new content
    new_header_content = f"""
    <div class="o_account_reports_header" style="direction:rtl;margin-top: 20px; margin-bottom: 10px;text-align:center">
    <table width="98%">
    <tr>
        <td width="70%">
               <table style="text-align: center;width: 100%;">
                        <tr>
                            <td colspan="4" style="font-weight: bold;font-size:1.8em;padding-top:20px;">كشف حساب عميل</td>
                        </tr>
                        <tr>
                            <td colspan="1" style="font-weight: bold;padding-top:20px;">العميل </td>
                            <td colspan="3" style="text-align:right;padding-top:20px;">{options['selected_partner_ids']} </td>
                        </tr>
                        <tr>
                           <td style="font-weight: bold;padding-top:20px;">
                            فترة الكشف
                            </td>
                            <td style="padding-top:20px;">
                            من: {date_from}
                            </td>
                            <td colspan="2"  style="padding-top:20px;">
                            إلى: {date_to}
                            </td>
                        </tr>
                    </table>
        </td>
         <td style="text-align:left" width="30%">
        {logo_tag}
        </td>
    </tr>
    </table>
    
    </div>
    """

    # Parse the new content
    new_header_element = html.fromstring(new_header_content)

    # Replace the old content with the new one
    header_div_element.clear()
    header_div_element.append(new_header_element)

    # header_div_element = root.find('.//div[@class="o_account_reports_header"]')
    #
    # # Add style attribute
    # header_div_element.set("style", "text-align:center")

    body = etree.tostring(root, pretty_print=True, method="html", encoding="utf-8").decode()

    body = Markup(body)
    return body


def handle_footer(footer):
    return footer


class AccountReport(models.AbstractModel):
    _inherit = 'account.report'

    def get_pdf(self, options):

        #  /\_/\
        # ( ◕‿◕ )
        #  >   <
        # Beginning: Ehab

        if 'Partner Ledger' in self._get_report_name():
            if not config['test_enable']:
                self = self.with_context(commit_assetsbundle=True)

            base_url = self.env['ir.config_parameter'].sudo().get_param('report.url') or self.env[
                'ir.config_parameter'].sudo().get_param('web.base.url')
            rcontext = {
                'mode': 'print',
                'base_url': base_url,
                'company': self.env.company,
            }

            body_html = self.with_context(print_mode=True).get_html(options)
            body = self.env['ir.ui.view']._render_template(
                "account_reports.print_template",
                values=dict(rcontext, body_html=body_html),
            )
            footer = self.env['ir.actions.report']._render_template("web.internal_layout", values=rcontext)
            footer = self.env['ir.actions.report']._render_template("web.minimal_layout",
                                                                    values=dict(rcontext, subst=True,
                                                                                body=Markup(
                                                                                    footer.decode())))

            landscape = False
            # if len(self.with_context(print_mode=True).get_header(options)[-1]) > 5:
            #     landscape = True

            body = handle_body(self, body, options)  # (｡◔‿◔｡)
            footer = handle_footer(footer)  # (｡◔‿◔｡)

            return self.env['ir.actions.report']._run_wkhtmltopdf(
                [body],
                footer=footer.decode(),
                landscape=landscape,
                specific_paperformat_args={
                    'data-report-margin-top': 10,
                    'data-report-header-spacing': 10
                }
            )
        else:
            return super(AccountReport, self).get_pdf(options)
