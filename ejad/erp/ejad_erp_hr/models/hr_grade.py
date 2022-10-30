from odoo import api, fields, models


class HrGradeType(models.Model):
    _name = 'hr.grade.type'
    _description = 'Hr Grade Type'

    name = fields.Char(string="Name", required=True)
    code = fields.Char(string="Code", required=True)
    contract_type = fields.Selection([('sicetific', 'هيئة علمية '),
                                      ('management', 'ادارين'),
                                      ('staff', 'مهنين')], string="نوع العقد")


class HrGradeGrade(models.Model):
    _name = 'hr.grade'
    _description = 'Hr Grade'
    # _order = "sequence asc,id asc"

    sequence = fields.Integer('Sequence', default=10)
    grade = fields.Char(string="grade", required=True)
    grade_type_id = fields.Many2one('hr.grade.type', 'Grade Type', required=True)
    contract_type = fields.Selection([('sicetific', 'هيئة علمية '),
                                      ('management', 'ادارين'),
                                      ('staff', 'مهنين')], string="نوع العقد")

    name = fields.Char(compute='_compute_name', store=True)
    annual_allowance=fields.Float(string="العلاوة السنوية ", required=False)

    @api.depends('grade_type_id', 'grade')
    def _compute_name(self):
        for record in self:
            record.name = str(record.grade_type_id.code) + ' || ' + str(record.grade)

    # grade_type=fields.Selection([('SA','Scientific Authority'),('AD','Administration'),('SP','Specialization'),('PR','Profitable'),('OTHER','Other')],string=" Grade Type")
    description = fields.Text('Description')
    level_ids = fields.One2many('hr.grade.level', 'grade_id', 'Levels')


class HrGradeLevel(models.Model):
    _name = 'hr.grade.level'
    _description = 'Hr Grade Level'
    # _order = "sequence asc,id asc"

    sequence = fields.Integer('Sequence', default=10)
    level = fields.Char(string="Level", required=True)
    grade_id = fields.Many2one('hr.grade', 'Grade', required=True)
    level_sequence = fields.Integer('level seq', related='grade_id.sequence')

    name = fields.Char(compute='_compute_name', store=True)

    @api.depends('grade_id', 'level')
    def _compute_name(self):
        for record in self:
            record.name = str(record.grade_id.name) + " / " + str(record.level)

    grade_type_id = fields.Many2one('hr.grade.type', 'Grade Type', related='grade_id.grade_type_id',store=True)

    # grade_type=fields.Selection([('SA','Scientific Authority'),('AD','Administration'),('SP','Specialization'),('PR','Profitable'),('OTHER','Other')],string=" Grade Type")


    gross=fields.Float(string="Gross",required=True)

    allowance_in=fields.Float(string="انتداب داخلي ",required=False)
    allowance_out=fields.Float(string="انتداب خارجي",required=False)

    transfer_allowance=fields.Float(string="Transfer allowance", required=False)
    assignment_allowance=fields.Float(string="Assignment allowance", required=False)
    annual_allowance=fields.Float(string="Annual Allowance", required=False)
    internal_mandate = fields.Float(string="بدل انتداب داخلي" ,default=0)
    external_mandate = fields.Float(string="بدل انتداب خارجي" ,default=0)

    description = fields.Text('Description')
