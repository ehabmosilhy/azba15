# -*- coding: utf-8 -*-


import time
from odoo.exceptions import ValidationError
from odoo import api, fields, models, _
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from lxml import etree
import logging
_logger = logging.getLogger(__name__)

class HrEmployee(models.Model):
    _inherit = "hr.employee"

    emp_attendance_no = fields.Integer('Attendance No')
    work_time = fields.Many2one('resource.calendar', string='Working Time', related='resource_id.calendar_id')


class ResourceCalendar(models.Model):
    _inherit = 'resource.calendar'

    employees_ids = fields.One2many('hr.employee', 'work_time', 'Employees', required=True)
    working_hours = fields.Float(string='Deutey Hours', required=False, default=8)
    excuse = fields.Float(string='Excuse')
    priority = fields.Integer('Priority', help="Max priority For Basic calendar") # TODO required=True need migration script
    include_on_deduction = fields.Boolean(string='Included on Deduction')
    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')
    # Filter and Domain purpose
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other')
    ])
    job_id = fields.Many2one('hr.job', 'Job Position')
    category_ids = fields.Many2many('hr.employee.category', string='Tags')

    @api.onchange('gender', 'job_id', 'category_ids')
    def _onchange_user(self):
        domain = []
        if self.employees_ids:
            for emp in self.employees_ids:
                emp.work_time = False
        if self.gender:
            domain.append(('gender', '=', self.gender))
        if self.job_id:
            domain.append(('job_id', '=', self.job_id.id))
        if self.category_ids:
            domain.append(('category_ids', 'in', self.category_ids.ids))
        return {'domain': {'employees_ids': domain}}


class ResourceCalendarAttendance(models.Model):
    _inherit = "resource.calendar.attendance"

    rest = fields.Float(string='Rest period', help="Rest period within work time.")


class HrAttendance(models.Model):
    _name = "hr.attendance"
    _inherit = "hr.attendance"
    _order = "id desc"

    @api.model
    def get_check_in_out_data(self):
        # ddate = '01/09/2019'
        # ddate = str(ddate[3:5])+'/'+str(ddate[0:2])+str(ddate[5:])
        # print("   DDDAAAte ",str(ddate[3:5])+'/'+str(ddate[0:2])+str(ddate[5:]))

        try:
            import pymssql
            _logger.info("  pymssql 1111111111111111")
            conf = self.env['connect.mssql'].search([])
            if conf:
                # Connection Parameters
                conf = conf[0]
                my_server = conf.server_name
                my_user = conf.user_name
                my_database = conf.database_name
                my_password = conf.password
                _logger.info("  Old Data my_server"+ my_server)
                _logger.info("  Old Data my_user"+ my_user)
                _logger.info("  Old Data my_database"+ my_database)
                _logger.info("  Old Data my_password"+ my_password)
                cr = self._cr
                conn = pymssql.connect(server=my_server, user=my_user, password=my_password, database=my_database)
                _logger.info("  Connection 1111111111111111")
                cr.execute('select sql_server_id from hr_attendance where sql_server_id IS NOT NULL')
                _logger.info("  Old Data 1111111111111111")
                old_sql_result = cr.fetchall()
                old_sql = [osr[0] for osr in old_sql_result]
                _logger.info("  Old Data 2222222222" +str(old_sql) )
                cursor = conn.cursor()
                _logger.info("  Old Data 333333333333")
                my_query = 'select user_id,row,su_date_start,su_actual_in,su_actual_out from inoutrep'
                self._cr.execute('select emp_attendance_no,id from hr_employee where emp_attendance_no not in (0)')
                res1 = self._cr.fetchall()
                res2= dict(res1)
                # rows= [('100       ', 1, '01/09/2019', '06:40:00', '14:11:53'),
                #          ('1003      ', 2, '01/09/2019', '05:25:58', '17:35:47'),
                #          ('1004      ', 3, '01/09/2019', '05:54:04', '18:33:29'),
                #          ('1005      ', 4, '01/09/2019', '05:05:33', '17:35:38'),
                #          ('1006      ', 5, '01/09/2019', '05:44:26', '18:09:38'),
                #          ('1007      ', 6, '01/09/2019', '00:00:00', '00:00:00'),
                #          ('1009      ', 7, '01/09/2019', '08:48:50', '00:00:00'),
                #          ('1010      ', 8, '01/09/2019', '06:49:04', '15:11:19')]
                _logger.info("  Query  "+my_query)
                cursor.execute(my_query)

                rows = cursor.fetchall()
                _logger.info("  Exceute 1111111111111111" + str(rows))
                conn.close()
                att_obj = self.env['hr.attendance']
                for r in rows:
                    # cr.execute('select id from hr_employee where emp_attendance_no = %s', (int(r[1]),))
                    # res = cr.fetchone()
                    if res2 and (r[1] not in old_sql) and (int(r[0]) in res2):
                        ddate = str(r[2])
                        ddate = str(ddate[3:5]) + '/' + str(ddate[0:2]) + str(ddate[5:])
                        rec1 = att_obj.create(
                            {'sql_server_id': r[1],
                             'employee_id': res2[int(r[0])],
                             'check_in': (ddate + ' ' + str(r[3])),
                             #'check_in': (ddate + ' ' + str(r[3])),
                             'check_out': (ddate + ' ' + str(r[4]))})
                        #rec1.check_in = datetime.strptime(rec1.check_in, '%Y-%m-%d %H:%M:%S') - timedelta(hours=3)
                        #rec1.check_out = datetime.strptime(rec1.check_out, '%Y-%m-%d %H:%M:%S') - timedelta(hours=3)
                        # cr.execute(
                        #     'insert into hr_attendance (sql_server_id, employee_id, check_in, check_out) values '
                        #     '(%s, %s, %s, %s)',
                        #     (r[1], res2[int(r[0])], (ddate + ' ' + str(r[3])), (ddate + ' ' + str(r[4]))),
                        # )
                        _logger.info(' Every Things OK')
                    else:
                        _logger.info(' Not ok     ????????????????')
            return True
        except:
            _logger.info("An Error Occurred, please check your parameters!\n" \
                  "And make sure (pymssql) is installed (pip3 install pymssql).")
            return True

    # check_in = fields.Datetime(default=False)
    # check_out = fields.Datetime()

    computed_check_in = fields.Datetime(string="Check In.", compute='compute_check_in', store=True)
    computed_check_out = fields.Datetime(string="Check Out.", compute='compute_check_out', store=True)
    emp_attendance_no = fields.Integer(related='employee_id.emp_attendance_no', store=True)


    @api.depends('check_in')
    def compute_check_in(self):
        for rec in self:
            if rec.check_in:
                check_in = str(rec.check_in)
                rec.computed_check_in = datetime.strptime(check_in, '%Y-%m-%d %H:%M:%S') - timedelta(hours=3)
            else:
                rec.computed_check_in = False


    @api.depends('check_out')
    def compute_check_out(self):
        for rec in self:
            if rec.check_out:
                check_out = str(rec.check_out)
                rec.computed_check_out = datetime.strptime(check_out, '%Y-%m-%d %H:%M:%S') - timedelta(hours=3)
            else:
                rec.computed_check_out = False

    @api.constrains('check_in', 'check_out')
    def _check_validity_check_in_check_out(self):
        """ verifies if check_in is earlier than check_out. """
        for attendance in self:
            if False:
                print("")

    @api.constrains('check_in', 'check_out', 'employee_id')
    def _check_validity(self):
        """ Verifies the validity of the attendance record compared to the others from the same employee.
            For the same employee we must have :
                * maximum 1 "open" attendance record (without check_out)
                * no overlapping time slices with previous employee records
        """
        for attendance in self:
            if False:
                print("")


    def unlink(self):
        raise ValidationError(_('Deletion is forbbiden'))

    attendance_id = fields.Many2one('hr.attendance.record')
    sql_server_id = fields.Integer()

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        result = super(HrAttendance, self).fields_view_get(view_id, view_type, toolbar=toolbar, submenu=submenu)
        doc = etree.XML(result['arch'])
        if view_type != 'search' and not self.env.user.has_group('ejad_erp_hr.access_attendance_edit_create'):
            # root = etree.fromstring(result['arch'])
            doc.set('create', 'false')
            doc.set('edit', 'false')
            doc.set('delete', 'false')
        result['arch'] = etree.tostring(doc)
        return result


class HrAttendanceRecord(models.Model):
    _inherit = ['mail.thread']
    _name = "hr.attendance.record"
    _description = "Hr Attendance Record"

    employee_id = fields.Many2one('hr.employee', "Employee Name", required=True, index=1, readonly=True)
    date = fields.Date('Date', required=True, index=1, readonly=True)
    day_log = fields.One2many('hr.attendance', 'attendance_id', 'Day Log', readonly=True)
    worked_hours = fields.Float('Worked Hours', readonly=True)
    total_delay = fields.Float('Delay', readonly=True)
    diff_from_duety = fields.Float('Deduction Delay', readonly=True)
    early_hours = fields.Float('Early Hours', readonly=True)
    late_hours = fields.Float('Late Hours', readonly=True)
    signin = fields.Datetime('Sign In', readonly=True)
    signout = fields.Datetime('Sign out', readonly=True)
    deduction_amount = fields.Float('Deduction Amount', readonly=True)
    department_id = fields.Many2one(related='employee_id.department_id', string='Department', store=True)
    # reason = fields.Many2one('hr.action.reason', "Reason", readonly=True,
    #                          states={'draft': [('readonly', False)]})
    absence_type = fields.Selection(
        [('holiday', 'Holiday'), ('excuse', 'Excuse'), ('no_delay', 'No Delay'), ('delay', 'Delay'),
         ('exceptional', 'Exceptional'), ('absent', 'Absent'), ('public_holiday', 'Public Holiday'),
         ('training', 'Training'), ('mission', 'Mission')], 'Absence Type')
    excuse_seconds = fields.Float('Excuse Seconds', readonly=True)
    comment = fields.Text('Notes')
    state = fields.Selection(
        [('draft', 'Draft'), ('confirm', 'Confirmed'), ('approve', 'Approved'), ('no_delay', 'No delay')], 'Status',
        default='draft', required=True, readonly=True)
    active = fields.Boolean('Active', default=True)
    duty_time = fields.Many2one('resource.calendar.attendance', "Resource Calendar Attendance", readonly=True)
    payslip_id = fields.Many2one('hr.payslip', string='Payslips', readonly=True)


    def unlink(self):
        raise ValidationError(_('Deletion is forbbiden'))


    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, _("%(empl_name)s / %(date)s / %(duty_time)s") % {
                'empl_name': record.employee_id.name,
                'date': record.date,
                'duty_time': record.duty_time.name,
            }))
        return result

    def to_date_time(self, float_time, like):
        """ change float time to date time
            Arguments:
            `float time `: the time to chang as Ex 8.5 --> 8:30
            `like`: the date time that to be like it as Ex 5/10/2016 09:10:15

            Return:
            date time with the date of like and time of float time
            5/10/2016 8:30:00
        """
        hours = int(float_time)
        minutes = str((int(str(float_time).split('.')[1])) * 60)
        if len(minutes) > 2:
            minutes = minutes[:2]
        if len(minutes) == 1:
            minutes += "0"
        date = str(str(like).split(' ')[0])
        date_time = date + ' ' + str(hours) + ':' + str(minutes) + ':00'
        # return fields.Datetime.from_string(str(date_time)).date()
        return datetime.strptime(str(date_time), "%Y-%m-%d %H:%M:%S").date()

    def to_minutes(self, float_time):
        """ change float time to minutes
        Arguments:
        `float time `: the time to chang as Ex 8.5 --> 8:30
        """
        return float(float_time) * 60

    def calculate_delay(self, emp_id, date, sign_in, sign_out, calendar, duety_hour_from, deuty_hour_to):
        working_hours, delay, early_hours, delay_on_morning, late_hours = 0, 0, 0, 0, 0
        duety_hour_from = self.to_date_time(duety_hour_from, sign_in)
        deuty_hour_to = self.to_date_time(deuty_hour_to, sign_in)
        if duety_hour_from and deuty_hour_to:
            duety_hours = (deuty_hour_to - duety_hour_from).seconds
            working_hours = (sign_out - sign_in).seconds
            if sign_in < duety_hour_from:
                early_hours = (duety_hour_from - sign_in).seconds
                working_hours -= early_hours

            if sign_out > deuty_hour_to:
                late_hours = (sign_out - deuty_hour_to).seconds
                working_hours -= late_hours

            if sign_in > deuty_hour_to:
                working_hours -= working_hours

            if sign_in > duety_hour_from:
                delay_on_morning = (sign_in - duety_hour_from).seconds

            delay = (duety_hours - working_hours)

        return delay_on_morning, early_hours, late_hours, delay, working_hours


    def get_emp_attendance(self, employee_id, record_date, hour_from, hour_to):
        result = {}
        cal_date_from = self.to_date_time(hour_from, record_date)
        cal_date_to = self.to_date_time(hour_to, record_date)
        self.env.cr.execute("""
                    SELECT id,check_in,check_out 
                    FROM hr_attendance
                    WHERE employee_id=%s
                        AND( (check_in between %s AND %s)
                        OR   (check_out between %s AND %s)
                        OR   ( %s between check_in AND check_out 
                            AND %s between check_in AND check_out) ) """,
                            (employee_id.id, cal_date_from, cal_date_to, cal_date_from, cal_date_to, cal_date_from,
                             cal_date_to))
        result = self.env.cr.dictfetchall()
        #print("      QQQQQQ       ",result)
        return result


    def get_calendar(self, emp, att_date):
        resource_calendar = self.env['resource.calendar']
        resource_calendar_ids = resource_calendar.search([])
        if resource_calendar_ids:
            resource_calendar_priority = resource_calendar_ids.sorted(key=lambda x: x.priority, reverse=True)
            for calendar in resource_calendar_priority:
                date_from = fields.Date.from_string(calendar.start_date)
                date_to = fields.Date.from_string(calendar.end_date)
                if date_from and date_to:
                    if att_date >= date_from and att_date <= date_to:
                        if emp.id in calendar.employees_ids.ids:
                            return calendar
                elif date_from and not date_to:
                    if att_date >= date_from:
                        if emp.id in calendar.employees_ids.ids:
                            return calendar
                elif not date_from and date_to:
                    if att_date <= date_to:
                        if emp.id in calendar.employees_ids.ids:
                            return calendar
                else:
                    if emp.id in calendar.employees_ids.ids:
                        return calendar


    def get_attendance_calendar(self, emp, att_date, calendar):
        attendance_calendar = self.env['resource.calendar.attendance']
        result = []
        weekday = str(att_date.weekday())

        attendance_calendar_ids = attendance_calendar.search(
            [('calendar_id', '=', calendar.id), ('dayofweek', '=', weekday)])
        for attendance in attendance_calendar_ids:
            date_from = fields.Date.from_string(attendance.date_from)
            date_to = fields.Date.from_string(attendance.date_to)
            if date_from and date_to:
                if att_date >= date_from and att_date <= date_to:
                    result.append(attendance)
            elif date_from:
                if att_date >= date_from:
                    result.append(attendance)
            elif date_to:
                if att_date <= date_to:
                    result.append(attendance)
            else:
                result.append(attendance)
        return result


    def create_attendance_record(self, employees_ids, att_date):
        record = self.env['hr.attendance.record']
        global_leave = {}
        att_date = str(att_date).split(' ')[0]
        att_date = fields.Date.from_string(att_date)
        for emp in employees_ids:
            calendar = self.get_calendar(emp, att_date)
            if not calendar:
                raise ValidationError(_('This employee has no calendar %s') % (emp.name))
            # get all attendance calendar in day
            attendance_calendar = self.get_attendance_calendar(emp, att_date, calendar)
            if attendance_calendar:
                for res in attendance_calendar:
                    basicTrue = record.search(
                        [('date', '=', att_date), ('employee_id', '=', emp.id), ('duty_time', '=', res.id),
                         ('active', '=', False)])
                    basicFalse = record.search(
                        [('date', '=', att_date), ('employee_id', '=', emp.id), ('duty_time', '=', res.id),
                         ('active', '=', True)])
                    recordId = basicTrue + basicFalse
                    if not recordId:
                        recordId = record.create({'employee_id': emp.id, 'date': att_date, 'duty_time': res.id})
                    recordId.record_calculate()
        return True


    def process_attendance_record(self, start_date, end_date, employees_ids):
        start_date = str(start_date).split(' ')[0]
        end_date = str(end_date).split(' ')[0]
        if start_date > end_date:
            raise ValidationError(_('start date must be before end date'))
        if not employees_ids:
            return []
        while start_date <= end_date:
            start_date = datetime.strptime(str(start_date), "%Y-%m-%d")
            self.create_attendance_record(employees_ids, start_date)
            start_date += relativedelta(days=1)
            start_date = str(start_date).split(' ')[0]
        return True


    def record_calculate(self):
        hr_holidays = self.env['hr.leave']
        hr_attendance = self.env['hr.attendance']
        calendar_leaves = self.env['resource.calendar.leaves']
        for record in self:
            vals = {}
            emp = record.employee_id
            # TODO:no employee state yet
            # if record.employee_id.state == 'refuse':
            #     continue

            end_date = record.date.strftime('%Y-%m-%d 10:00:00')
            start_date = record.date.strftime('%Y-%m-%d 23:59:59')
            # get Holidays
            holidays_days = hr_holidays.search(
                [('employee_id', '=', emp.id), ('date_from', '<=', start_date), ('date_to', '>=', end_date),
                 ('state', 'in', ('validate', 'done_cut', 'approve_cut', 'cut'))])
            holidays = holidays_days and True or False
            excuse_seconds = 0
            full_holidays = False
            public_holiday, full_public_holiday = False, False
            if holidays:
                # TODO:excuse,misstion
                # for holiday in holidays:

                #     if holiday.holiday_status_id.absence:
                #         excuse_seconds += (self.to_minutes(holiday.number_hours))*60.0
                #     else:
                full_holidays = True
            # Public Holidays
            duty_from = self.to_date_time(record.duty_time.hour_from, record.date)
            duty_to = self.to_date_time(record.duty_time.hour_to, record.date)
            leaves = calendar_leaves.search([('calendar_id', '=', record.duty_time.calendar_id.id)])
            for leave in leaves:
                date_from = fields.Datetime.from_string(leave.date_from)
                date_to = fields.Datetime.from_string(leave.date_to)
                if duty_from >= date_from and duty_to <= date_to:
                    full_public_holiday = True
                elif date_from >= duty_from and date_to <= duty_to:
                    public_holiday = True
                elif duty_to >= date_from and duty_to <= date_to:
                    public_holiday = True
                elif duty_from >= date_from and duty_from <= date_to:
                    public_holiday = True

            # get attendance related to attendance calendar
            emp_attendance = self.get_emp_attendance(emp, record.date, record.duty_time.hour_from,
                                                     record.duty_time.hour_to)
            if emp_attendance:
                signin, signout, early_hours, late_hours, working_hours, delay = 0, 0, 0, 0, 0, 0
                att_ids = []
                sign_in = []
                sign_out = []
                for att in emp_attendance:
                    att_ids.append(att['id'])
                    sign_in.append(datetime.strptime(str(att['check_in']), "%Y-%m-%d %H:%M:%S"))
                    #print("  ##@@@@@@   ",att['check_out'])
                    if att['check_out']:
                        sign_out.append(datetime.strptime(str(att['check_out']), "%Y-%m-%d %H:%M:%S"))
                signin = min(sign_in)
                signout = max(sign_out)
                hr_attendance.browse(att_ids).write({'attendance_id': record.id})

                calendar = record.duty_time.calendar_id
                duety_hour_from = record.duty_time.hour_from
                deuty_hour_to = record.duty_time.hour_to
                duty_hours = deuty_hour_to - duety_hour_from
                if signin and signout:
                    delay_on_morning, early_hours, late_hours, delay, working_hours = self.calculate_delay(emp,
                                                                                                           record.date,
                                                                                                           signin,
                                                                                                           signout,
                                                                                                           calendar,
                                                                                                           duety_hour_from,
                                                                                                           deuty_hour_to)
                    vals['total_delay'] = delay / 3600.0
                    vals['signin'] = signin
                    vals['signout'] = signout
                    vals['early_hours'] = early_hours / 3600.0
                    vals['late_hours'] = late_hours / 3600.0
                elif signin:
                    vals['signin'] = signin
                elif signout:
                    vals['signout'] = signout

                if full_holidays:
                    # handel mission training,mission,
                    vals['diff_from_duety'] = 0
                    vals['absence_type'] = 'holiday'
                elif full_public_holiday:
                    vals['diff_from_duety'] = 0
                    vals['absence_type'] = 'public_holiday'

                elif working_hours > 0.0:
                    excuse_within_duety = self.to_minutes(calendar.excuse) * 60
                    if excuse_within_duety > 0:
                        include_on_deduction = calendar.include_on_deduction
                        if delay_on_morning > 0 and not include_on_deduction:
                            if delay_on_morning >= excuse_within_duety:
                                delay -= excuse_within_duety
                            else:
                                delay -= delay_on_morning
                        elif delay_on_morning > 0 and include_on_deduction:
                            if delay_on_morning <= excuse_within_duety:
                                delay -= delay_on_morning
                    vals['diff_from_duety'] = (delay - excuse_seconds) / 3600.0
                    if vals['diff_from_duety'] <= 0 and excuse_seconds > 0:
                        vals['absence_type'] = 'excuse'
                        vals['excuse_seconds'] = excuse_seconds / 60.0
                    elif vals['diff_from_duety'] <= 0:
                        vals['absence_type'] = 'no_delay'
                    else:
                        vals['absence_type'] = 'delay'
                else:
                    if duty_hours <= 0.0:
                        vals['diff_from_duety'] = duty_hours
                        vals['total_delay'] = duty_hours
                        vals['absence_type'] = 'exceptional'
                    elif (working_hours == 0 and excuse_seconds > 0):
                        vals['diff_from_duety'] = duty_hours - (excuse_seconds) / 3600.0
                        vals['excuse_seconds'] = excuse_seconds / 60.0
                    else:
                        vals['absence_type'] = 'absent'
                        vals['diff_from_duety'] = duty_hours
                        vals['total_delay'] = duty_hours

                emp_salry_per_minute = 0
                deduction_delay = (self.to_minutes(vals['diff_from_duety']))
                if deduction_delay < 1:
                    vals['state'] = 'no_delay'
                    vals['active'] = False
                else:
                    vals['state'] = 'draft'
                    vals['active'] = True
                vals['deduction_amount'] = 0.0
                vals['worked_hours'] = working_hours / 3600.0
                if vals['diff_from_duety'] < 0:
                    vals['diff_from_duety'] = 0
                record.write(vals)
        return True


    def reload(self):
        self.create_attendance_record(self.employee_id, self.date)
        return True


class HrAttendanceRecord(models.Model):
    _inherit = 'hr.attendance.record'


    def record_scheduler(self):
        time = datetime.now() - relativedelta(days=1)
        date = time.strftime('%Y-%m-%d')
        employee_ids = self.env['hr.employee'].search([])
        record = self.env['hr.attendance.record'].process_attendance_record(date, date, employee_ids)
        return True
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
