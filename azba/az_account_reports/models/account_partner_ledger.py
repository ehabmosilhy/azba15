# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from markupsafe import Markup
from odoo import models, api, _
from odoo.tools import config
from lxml import etree, html


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
            s.append(options['selected_partner_ids'][i] + f"[{partner_codes[i]}")
        options['selected_partner_ids'] = s

    @api.model
    def _get_report_name(self):
        return 'Partner Ledger كشف حساب عميل'


def handle_body(body, options):
    date_from = options.get('date').get('date_from')
    date_to = options.get('date').get('date_to')

    body_str = str(body)
    body_str = body_str.replace("SR", "")
    body_str = body_str.replace("</body>", """
     <footer style="text-align:center; font-size: large;width:90%;margin: auto;border:1px solid black;">
            نوافق على صحة الرصيد أعلاه .. وإذا لم نستلم منكم أى اعتراض على صحة هذا الكشف خلال أسبوع من تاريخه يعتبر الحساب صحيحاً ما عدا السهو والخطأ
        </footer>
        </body>
    """)

    # Parse the HTML
    root = html.fromstring(body_str)

    # Find the element you want to replace
    div_element = root.find('.//div[@class="row print_only"]')

    # Your new content
    new_content = f"""
    <table>
        <tr>
            <td colspan="1">العميل </td>
            <td colspan="3">{options['selected_partner_ids']} </td>
        </tr>
        <tr>
            <td>
            فترة الكشف
            </td>
            <td>
            من: {date_from}
            </td>
            <td>
            إلى: {date_to}
            </td>
        </tr>
    </table>
    """

    # Parse the new content
    new_element = html.fromstring(new_content)

    # Replace the old content with the new one
    div_element.clear()
    div_element.append(new_element)
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

            body = handle_body(body, options)  # (｡◔‿◔｡)
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
