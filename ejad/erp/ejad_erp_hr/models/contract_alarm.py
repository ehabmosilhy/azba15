#-*- coding:utf-8 -*-

##############################################################################
#
#    Copyright (C) Appness Co. LTD **hosam@app-ness.com**. All Rights Reserved
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import api, fields, models
from datetime import date, datetime

class hr_contract_alarm(models.Model):
    _name = 'hr.contract.alarm'
    _description = 'Hr Contract Alarm'
    _inherit = ['mail.thread', 'resource.mixin']
    _rec_name = 'remain'
    _order = 'end_date asc'


    @api.model
    def contract_check(self):
        fmt = '%Y-%m-%d'
        current_date=datetime.today()
        #current_date=str(current_date)
        d1 = datetime.strptime(str(current_date.date()), '%Y-%m-%d')
        contract_object=self.env['hr.contract']
        alarm_object=self.env['hr.contract.alarm']

        contract_line_ids=contract_object.search(['|',('date_end','!=',False),('trial_date_end','!=',False)])
        for contract_line_id in contract_line_ids:
            contract_brws=contract_line_id
            flag= True
            end_date = str(contract_brws.date_end)
            if end_date:
                #print('$$$$$######       00000')
                end_date=datetime.strptime(end_date, '%Y-%m-%d')
                d2 = end_date
                diff=str((d2-d1).days)
                #print('$$$$$######       1111')
                if diff=='32':
                    alarm_object.create({'employee_id':contract_brws.employee_id.id,'contract_id':contract_brws.id,'remain':'32 days','state':'n','end_date':str(end_date)})
                    #alarm_object._needaction_domain_get
                    flag= False
                elif diff=='45':
                    alarm_object.create({'employee_id':contract_brws.employee_id.id,'contract_id':contract_brws.id,'remain':'45 days','state':'n','end_date':str(end_date)})
                    #alarm_object._needaction_domain_get
                    flag= False
            elif flag:
                end_date=contract_brws.trial_date_end
                if end_date:
                #end_date=str(end_date)
                    #print('&&&%%%@%@%    ',contract_brws.employee_id.name)
                    d2 = datetime.strptime(end_date, '%Y-%m-%d')
                    diff=str((d2-d1).days)
                    if diff=='7':
                        alarm_object.create({'employee_id':contract_brws.employee_id.id,'contract_id':contract_brws.id,'remain':'7 days','state':'n','end_date':str(end_date)})
                        #alarm_object._needaction_domain_get
                        flag= False
                    elif diff=='12':
                        alarm_object.create({'employee_id':contract_brws.employee_id.id,'contract_id':contract_brws.id,'remain':'12 days','state':'n','end_date':str(end_date)})
                        #alarm_object._needaction_domain_get
                        flag= False


    @api.depends('state','remain')
    def done(self):
        if self.state=='n':
            self.state='d'
        if self.remain=="7 days":
            self.remain="7 days -"
        elif self.remain=="32 days":
            self.remain="32 days -"
        elif self.remain=="45 days":
            self.remain="45 days -"
        elif self.remain=="12 days":
            self.remain="12 days -"
        #self.contract_check()
            
    contract_id = fields.Many2one('hr.contract',string="Contract",)
    employee_id = fields.Many2one('hr.employee', string="Employee", )
    state=fields.Selection([('n','in progress'),('d','done')], string="state")
    remain=fields.Char(string='remaining days')
    end_date=fields.Date(string="End Date")



