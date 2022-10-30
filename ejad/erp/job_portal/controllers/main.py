# See LICENSE file for full copyright and licensing details.

"""
This is controller file to enahnce Website Recruitment portal of Odoo.
.
"""
import base64
import werkzeug.utils
from datetime import datetime

import odoo.addons.website_sale.controllers.main
from odoo import SUPERUSER_ID, http, _
from odoo.addons.portal.controllers.portal \
    import CustomerPortal as CustomerPortal, pager as portal_pager
from odoo.addons.website_hr_recruitment.controllers.main \
    import WebsiteHrRecruitment as Home
from odoo.http import request
from odoo.exceptions import AccessError, MissingError, ValidationError

class InheritedCustomerPortal(CustomerPortal):
    """Updated the Optional fields list to stop the unkown fields error."""

    OPTIONAL_BILLING_FIELDS = ["zipcode", "state_id", "vat", "company_name",
                               "organization",
                               "contact_referee", "location", "study_field",
                               "position_referee",
                               "name_referee", "grade", "job_position",
                               "start_date", "description",
                               "end_date", "qualification", "certification",
                               'operation_type', 'opr_id', 'tr_no',
                               'middlename', 'lastname', 'is_still']

    def _prepare_portal_layout_values(self):
        values = super(InheritedCustomerPortal, self)._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        applicant_obj = request.env['hr.applicant']
        application_count = applicant_obj.sudo().search_count(
                    [('email_from', '=', partner.email)])
        values.update({
            'application_count': application_count,
        })
        return values

    @http.route(['/my/applications', '/my/applications/page/<int:page>'],
                type='http', auth="user", website=True)
    def portal_my_applicantions(self, page=1, sortby=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        applicant_obj = request.env['hr.applicant']
        domain = [('email_from', '=', partner.email)]
        searchbar_sortings = {
            'job': {'label': _('Applied Job'), 'order': 'job_id'},
            'department': {'label': _('Department'), 'order': 'department_id'},
        }

        # default sortby order
        if not sortby:
            sortby = 'job'
        sort_order = searchbar_sortings[sortby]['order']

        archive_groups = self._get_archive_groups('hr.applicant', domain)

        # count for pager
        application_count = applicant_obj.search_count(domain)
        # make pager
        pager = portal_pager(
            url="/my/applications",
            url_args={'sortby': sortby},
            total=application_count,
            page=page,
            step=self._items_per_page
        )
        # search the count to display, according to the pager data
        applications = applicant_obj.search(domain, order=sort_order,
                                            limit=self._items_per_page,
                                            offset=pager['offset'])
        request.session['my_leads_history'] = applications.ids[:100]

        values.update({
            'applications': applications.sudo(),
            'pager': pager,
            'page_name': 'Applications',
            'archive_groups': archive_groups,
            'default_url': '/my/applications',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
        })
        return request.render("job_portal.portal_my_application", values)

    @http.route(['/my/applications/<int:application_id>'], type='http',
                auth="user", website=True)
    def portal_application_page(self, application_id, **kw):
        application = request.env['hr.applicant'].sudo().search(
            [('id', '=', application_id)])
        values = {
            'partner_id': request.env.user.partner_id.id,
            'application': application,
            'page_name': 'Applications',
        }
        return request.render('job_portal.portal_job_application', values)


class WebsiteHrRecruitment(Home):
    """This class is defined to enhance HR Recruitment portal."""

    @http.route('/jobs/apply/<model("hr.job"):job>', type='http',
                auth="user", website=True)
    def jobs_apply(self, job, **kwargs):
        """A Method for the users to be able to apply for job.

        Args:
            job: The first parameter to fetch the job position.
            kwargs: The second parameter to get the details of
            the job applicant.

        Returns:
            It renders the template & creates a record for job
            application.
        """
        error = {}
        default = {}
        env = request.env(context=dict(request.env.context,
                                       show_address=True, no_tag_br=True))
        applicant_1 = request.env['hr.applicant'] \
            .search([('partner_id', '=', request.env.user.partner_id.id)],
                    limit=1, order='create_date desc')
        countries = env['res.country'].sudo().search([])
        states = env['res.country.state'].sudo().search([])
        inistitue = env['hr.institute'].sudo().search([])
        specializations =env['hr.specializations'].sudo().search([])
        sectors = env['hr.sectors'].sudo().search([])

        if 'website_hr_recruitment_error' in request.session:
            error = request.session.pop('website_hr_recruitment_error')
            default = request.session.pop('website_hr_recruitment_default')

        return request.render("website_hr_recruitment.apply", {
            'applicant': applicant_1,
            'job': job,
            'error': error,
            'default': default,
            'countries': countries,
            'states': states,
            'sectors':sectors,
            'specializations':specializations,
            'inistitue': inistitue,
            'partner': request.env['res.users'].sudo().browse(
                request.uid).partner_id,
        })

    def _get_applicant_char_fields(self):
        """A Helper Method to get the applicants's Char fields."""
        # 'partner_mobile', 'email_from',
        return ['middlename', 'lastname','familyname', 'gender', 'place_of_birth'
                , 'partner_mobile', 'email_from',
                'identification_id',#'IdEndDate',
                'arabic_level','english_level']

    def _get_applicant_boolean_fields(self):
        """A Helper Method to get the applicants's Booleans fields."""
        return ['is_same_address']

    def _get_applicant_relational_fields(self):
        """A Helper Method to get the applicants's Relational fields."""
        return ['department_id', 'job_id', 'country_id', 'state_id_ht']

    def _get_applicant_files_fields(self):
        """A Helper Method to get the applicants's File fields."""
        return ['ufile']

    def _get_residential_address(self, kwargs):
        """A Helper Method to get the applicants's residential address."""
        address = {
            'name': kwargs.get('firstname'),
            'street': kwargs.get('street'),
            'street2': kwargs.get('street2') or '',
            'city': kwargs.get('city'),
            'zip': kwargs.get('zip'),
            'state_id': kwargs.get('state_id'),
            'country_id': kwargs.get('country_id'),
            'mobile': kwargs.get('partner_mobile'),
            'email': kwargs.get('email_from'),
            'customer': False,
        }
        return address

    def _format_date(self, date):
        """A Helper Method to get the formated value of the date."""
        if date:
            return datetime.strptime(date, "%m/%d/%Y").isoformat(' ')
        return False

    @http.route('/test', type='http', auth="public",
                website=True)
    def test(self, **kwargs):
        return request.render("auth_signup.signup", {})

    @http.route('/jobs/thankyou', methods=['POST'], type='http', auth="public",
                website=True)
    def jobs_thankyou(self, **kwargs):
        """A Method for rendering thankyou template after applying for the job.replace
        Args:
            kwargs: The second parameter to get the details of
            the job applicant.

        Returns:
            It renders the template & creates a record for job
            application also attaches the applicant's attachment to the object.

        """
        # public user can't create applicants
        application = request.env['hr.applicant']
        error = {}
        default = {}
        env = request.env(context=dict(request.env.context,
                                       show_address=True, no_tag_br=True))
        applicant_1 = request.env['hr.applicant'] \
            .search([('partner_id', '=', request.env.user.partner_id.id)],
                    limit=1, order='create_date desc')
        countries = request.env['res.country'].sudo().search([])
        states = request.env['res.country.state'].sudo().search([])
        inistitue = request.env['hr.institute'].sudo().search([])
        specializations = request.env['hr.specializations'].sudo().search([])
        sectors = request.env['hr.sectors'].sudo().search([])
        if not (request.env['hr.academic'].search([('partner_id', '=', request.env.user.partner_id.id)])):
            #  return request.render('job_portal.update_sorry', {})
            # raise ValidationError("Please Insert Academic Data First")
            error = {'uAcademic': 'uAcademic'}
            default = {}
            job = request.env['hr.job'].sudo().search([('id','=',int(kwargs.get('job_id')))])
            return request.render("job_portal.ErrorValidate", {
                'trypeOfError': "Academic",
                'error_message': "",
                'job':job,
            })
        #
        # if redundant_check:
        #     return request.render("website_hr_recruitment.thankyou", {})
        env = request.env(user=SUPERUSER_ID)
        partner = env['res.partner'].sudo().browse(int(kwargs.get('partner_id')))
        vals = {
            'source_id': env.ref('job_portal.source_website_company').id,
            'name': kwargs.get('firstname') + "'s application",
            'partner_name': kwargs.get('firstname') + " " + kwargs.get('middlename') + " " + kwargs.get('lastname') + " " + kwargs.get('familyname') or '',
            'gender': kwargs.get('gender'),
            'birthday': kwargs.get('birthday'),
            'email_from': kwargs.get('email_from'),
            'middlename': kwargs.get('middlename'),
            'lastname': kwargs.get('lastname'),
            'familyname': kwargs.get('familyname'),

            'academic_ids': [(6, 0, partner.academic_ids.ids)],
            'experience_ids': [(6, 0, partner.experience_ids.ids)],
            'skills_ids': [(6, 0, partner.skills_ids.ids)],
            'country_id': partner.country_id.id,
            'partner_id': partner.id,
        }

        env = request.env(context=dict(request.env.context,
                                       show_address=True, no_tag_br=True))

        for field in self._get_applicant_boolean_fields():
            if kwargs.get(field) == 'on':
                vals[field] = True

        for field in self._get_applicant_char_fields():
            vals[field] = kwargs.get(field)

        for field in self._get_applicant_relational_fields():
            vals[field] = int(kwargs.get(field) or False)
        state = False
        # added condition for state value because it consider blank space.
        #if kwargs.get('state_id', False) != '':
         #   state = kwargs.get('state_id', False)
        vals['middlename'] = kwargs.get('middlename')
        vals['lastname'] = kwargs.get('lastname')
        vals['familyname'] = kwargs.get('familyname')
        vals['identification_id'] = kwargs.get('identification_id')
        #vals['IdEndDate'] = kwargs.get('IdEndDate')
        vals['marital'] = kwargs.get('marital')
        vals['gender'] = kwargs.get('gender')
        vals['birthday'] = kwargs.get('birthday')
        vals['partner_phone'] = kwargs.get('partner_phone')

        partner.write({'middlename': kwargs.get('middlename'), 'lastname': kwargs.get('lastname'),'familyname': kwargs.get('familyname'),
                     #  'country_id': kwargs.get('country_id'),
                      # 'state_id': kwargs.get('state_id'),

                       })
        redundant_check = application.sudo().search([('email_from', '=', kwargs.get('applicant_email'))], limit=1).id
        if redundant_check:
            redundant = application.sudo().search(
                [('email_from', '=', kwargs.get('email_from')), (
                    'job_id', '=', int(kwargs.get('job_id')))], limit=1).id
            if redundant:
                applicant_1 = application.sudo().search(
                    [('partner_id', '=', request.env.user.partner_id.id)],
                    limit=1, order='create_date desc')
                applicant_1.write(vals)
                return request.render('job_portal.update_sorry', {})


        applicant_id = application.sudo().create(vals).id

        for field_name in self._get_applicant_files_fields():
            if kwargs[field_name]:
                attachment_vals = {
                    'name': kwargs[field_name].filename,
                    'res_name': vals['name'],
                    'res_model': 'hr.applicant',
                    'res_id': applicant_id,
                    'datas': base64.encodestring(kwargs[field_name].read()),
                }
                env['ir.attachment'].create(attachment_vals)


        return request.render("website_hr_recruitment.thankyou", {})


class WebsiteInherit(odoo.addons.web.controllers.main.Home):
    """This class is defined to enhance HR Recruitment portal."""

    @http.route(['/post_resume'], type='http', auth="public", website=True)
    def post_resume(self, **kwargs):
        """A Method to post the resume."""
        return request.render("job_portal.social_info",
                              {'page_from': 'resume'})

    @http.route(['/post_job'], type='http', auth="user", website=True)
    def post_job(self, **kwargs):
        """A Method for Posting the Job from website portal.

        Args:
            kwargs: The second parameter to get the details of
            the job posting.

        Returns:
            It renders the posting job template & takes the process further.
        """
        if request.env.user in request.env.ref("hr_recruitment.group_hr_recruitment_manager").users:
            return request.render("job_portal.post_resume",
                                  {
                                      'post_job_active': True,
                                      'page_from': 'job',
                                      'job_department': request.env[
                                          'hr.department'].sudo().search([]),
                                      'job_type': request.env[
                                          'hr.job.type'].sudo().search([]), })
        else:
            return request.redirect('/')

    @http.route(['/add_academic_applicant'], type='json', auth="public",
                website=True)
    def add_academic_applicant(self, **kwargs):
        """A Method used to add Academic details of the applicant.

        Returns:
            It returns True after creating the record for
            the education of the applicant.
        """
        vals = {
            'name': request.env['res.users'].browse(
                request.uid).partner_id.name,
            'inistitue': kwargs.get('inistitue'),
            'country_id': kwargs.get('country_id'),
            'state_id': kwargs.get('state_id'),
            'study_field': kwargs.get('study_field'),
            'qualification': kwargs.get('qualification'),
            'study_field': kwargs.get('study_field'),
            'grade': kwargs.get('grade'),
            'start_date': kwargs.get('start_date'),
            'end_date': kwargs.get('end_date'),
            'partner_id': request.env['res.users'].browse(
                request.uid).partner_id.id,
        }
        if kwargs.get('end_date'):
            vals.update({'end_date': kwargs.get('end_date')})
        if kwargs.get('is_still'):
            vals.update({'is_still': True})
        else:
            vals.update({'is_still': False})
        print("############## vals #############")
        print(vals)
        print("############## vals #############")

        return request.env['hr.academic'].sudo().create(vals).id

    @http.route(['/edit_academic_applicant'], type='json', auth="public",
                website=True)
    def edit_academic_applicant(self, **kwargs):

        """A Method used to Edit Academic details of the applicant.

        Returns:
            It returns True after updating the record for
            the education of the applicant.
        """
        vals = {
            'inistitue': kwargs.get('inistitue'),
            'country_id': kwargs.get('country_id'),
            'state_id': kwargs.get('state_id'),
            'study_field': kwargs.get('study_field'),
            'qualification': kwargs.get('qualification'),
            'study_field': kwargs.get('study_field'),
            'grade': kwargs.get('grade'),
            'start_date': kwargs.get('start_date'),
            'end_date': kwargs.get('end_date'),
            'partner_id': request.env['res.users'].browse(
                request.uid).partner_id.id,
        }
        if kwargs.get('end_date'):
            vals.update({'end_date': kwargs.get('end_date')})
        if kwargs.get('is_still'):
            vals.update({'is_still': True})
            vals.update({'end_date': None})
        else:
            vals.update({'is_still': False})
        request.env['hr.academic'].sudo().browse(int(kwargs.get('id'))).write(vals)
        return kwargs.get('id')

    @http.route(['/delete_academic'], type='json', auth="public",
                website=True)
    def delete_academic(self, **kwargs):
        """A Method used to Delete Academic detail of the applicant.

        Returns:
            It returns True after creating the record for
            the education of the applicant.
        """
        return request.env['hr.academic'].sudo().browse(
            kwargs.get('id')).unlink()

    @http.route(['/add_experience'], type='json', auth="public",
                website=True)
    def add_experience(self, **kwargs):
        """A Method used to add Experience Details of the applicant.

        Returns:
            It returns True after creating the record for
            the Experience Details of the applicant.
        """

        vals = {
            'name': kwargs.get('job_position'),
            'job_position': kwargs.get('job_position'),
            'country_id': kwargs.get('country_id'),
            'state_id': kwargs.get('state_id'),
            'address': kwargs.get('address'),
            'company_name': kwargs.get('company_name'),
            'sector_id': kwargs.get('sector_id'),
            'description': kwargs.get('description'),
            'start_date': kwargs.get('start_date'),
            'partner_id': request.env['res.users'].browse(
                request.uid).partner_id.id,
        }
        if kwargs.get('end_date'):
            vals.update({'end_date': kwargs.get('end_date'), 'is_still': False})
        if kwargs.get('is_still'):
            vals.update({'end_date': None, 'is_still': True})
        else:
            vals.update({'is_still': False})
        return request.env['hr.experience'].sudo().create(vals).id

    @http.route(['/edit_experience_applicant'], type='json', auth="public",
                website=True)
    def edit_experience_applicant(self, **kwargs):
        """A Method used to Edit Experience details of the applicant.

        Returns:
            It returns True after updating the record for
            the Experience of the applicant.
        """

        vals = {
            'name': kwargs.get('job_position'),
            'referee_contact': kwargs.get('contact_referee'),
            'description': kwargs.get('description'),
            'referee_position': kwargs.get('position_referee'),
            'referee_name': kwargs.get('name_referee'),
            'notice_period': kwargs.get('notice_period'),
            'organization': kwargs.get('organization'),
            'location': kwargs.get('location'),
            'start_date': kwargs.get('start_date'),
            'partner_id': request.env['res.users'].browse(
                request.uid).partner_id.id,
            'type': kwargs.get('type'),
        }
        if kwargs.get('end_date') and not kwargs.get('is_still'):
            vals.update({'end_date': kwargs.get('end_date')})
        if kwargs.get('is_still'):
            vals.update({'end_date': None, 'is_still': True})
        else:
            vals.update({'is_still': False})
        request.env['hr.experience'].sudo().browse(
            int(kwargs.get('id'))).write(vals)
        return int(kwargs.get('id'))

    @http.route(['/delete_experience'], type='json', auth="public",
                website=True)
    def delete_experience(self, **kwargs):
        """A Method used to Delete Experience of the applicant.

        Returns:
            It returns True after creating the record for
            the education of the applicant.
        """
        return request.env['hr.experience'].sudo().browse(
            kwargs.get('id')).unlink()

    @http.route(['/add_skills'], type='json', auth="public",
                website=True)
    def add_skills(self, **kwargs):
        """A Method used to add Certiifcation details of the applicant.

        Returns:
            It returns True after creating the record for
            the Certiifcation of the applicant.
        """

        vals = {
            'name': kwargs.get('name'),
            'skill_level': kwargs.get('skill_level'),
            'partner_id': request.env['res.users'].browse(
                request.uid).partner_id.id,
        }

        return request.env['hr.mewan_skills'].sudo().create(vals).id

    @http.route(['/edit_skills'], type='json', auth="public",
                website=True)
    def edit_skills(self, **kwargs):
        """A Method used to Edit Certification details of the applicant.

        Returns:
            It returns True after updating the record for
            the Certification of the applicant.
        """
        vals = {
            'skill_level': kwargs.get('skill_level'),
            'name': kwargs.get('name'),
            'partner_id': request.env['res.users'].browse(
                request.uid).partner_id.id,
        }

        request.env['hr.mewan_skills'].sudo().browse(int(kwargs.get('id'))).write(vals)
        return int(kwargs.get('id'))

    @http.route(['/delete_skills'], type='json', auth="public",
                website=True)
    def delete_skills(self, **kwargs):
        """A Method used to Delete Certification detail of the applicant.

        Returns:
            It returns True after creating the record for
            the education of the applicant.
        """
        return request.env['hr.mewan_skills'].sudo().browse(
            kwargs.get('id')).unlink()

    @http.route(['/page/get_state_applicant'], type='json', auth="public",
                website=True)
    def get_state_applicant(self, country_id, **kwargs):
        states = request.env['res.country.state'].search([('country_id.id', '=', country_id)])
        list = []
        for state in states:
            list.append({'id': state.id, 'name': state.name})
        return list

    @http.route(['/add_benefits'], type='json', auth="public", website=True)
    def add_benefits(self, **kwargs):
        """A Method used to add Benefits to the Job Posting.

        Returns:
            It returns True after creating the record for
            the benefits the Job Posting.
        """
        vals = {
            'name': kwargs.get('benefits'),
            'job_benefits_id': int(kwargs.get('job_id')),
        }
        benefits = request.env['hr.job.benefits'].sudo().create(vals)
        if benefits:
            request.env['hr.job'].sudo().browse(
                int(kwargs.get('job_id'))).sudo().write({
                'benefits_ids': [(4, 0, benefits.id)]})
        return True

    @http.route(['/add_job_requirements'], type='json', auth="public",
                website=True)
    def add_job_requirements(self, **kwargs):
        """A Method used to add Requirements to the Job Posting.

        Returns:
            It returns True after creating the record for
            the Requirements the Job Posting.
        """
        vals = {
            'name': kwargs.get('job_requirements'),
            'job_requirement_id': int(kwargs.get('job_id')),
        }
        requirement = request.env['hr.job.requirement'].sudo().create(vals)
        if requirement:
            request.env['hr.job'].sudo().browse(
                int(kwargs.get('job_id'))).sudo().write({
                'job_requirement_ids': [(4, 0, requirement.id)]})
        return True

    @http.route(['/add_job_location'], type='json', auth="public",
                website=True)
    def add_job_location(self, **kwargs):
        """A Method used to add Location to the Job Posting.

        Returns:
            It returns True after creating the record for
            the Location the Job Posting.
        """
        vals = {
            'name': kwargs.get('job_location'),
            'job_location_id': int(kwargs.get('job_id')),
        }
        location = request.env['hr.job.location'].sudo().create(vals)
        if location:
            request.env['hr.job'].sudo().browse(
                int(kwargs.get('job_id'))).sudo().write({
                'location_ids': [(4, 0, location.id)]})
        return True

    @http.route(['/create_job'], type='http', auth="public",
                methods=['POST'], website=True)
    def create_job(self, **kwargs):
        """A Method for creating the Job Posting from Website.
        Args:
            kwargs: The second parameter to get the details of
            the job posting.
        Returns:
            It renders the template & creates a record for job
            posting.
        """
        job = request.env['hr.job'].sudo().search(
            [('name', '=', kwargs.get('job_title'))])

        closing_date = datetime.strptime(kwargs.get('date1'), '%m/%d/%Y') \
            .strftime('%Y-%m-%d')
        vals = {
            'name': kwargs.get('job_title'),
            'department_id': int(kwargs.get('job_department')),
            'description': kwargs.get('requirements'),
            'job_by_area': kwargs.get('job_functional_area'),
            'notify_email': kwargs.get('notify_email'),
            'closing_date': closing_date,
        }

        if job:
            job.sudo().write(vals)
        else:
            job = request.env['hr.job'].sudo().create(vals)
        return request.render("job_portal.add_job_details", {'job': job})

    @http.route(['/add_job_details'], type='http', auth="public",
                methods=['POST'], website=True)
    def add_job_details(self, **kwargs):
        """A Method for the adding more job details to the job posting.

        It adds benefits, requirements & location of the job posting.

        Args:
            kwargs: The second parameter to get the details of
            the newly addeed details of the job posting.

        Returns:
            It renders the template & creates a record for new job posted.
        """
        job = request.env['hr.job']
        if kwargs.get('benefits'):
            vals = {
                'name': kwargs.get('benefits'),
                'job_benefits_id': int(kwargs.get('job_id')),
            }
            benefits = request.env['hr.job.benefits'].sudo().create(vals)
            if benefits:
                job.sudo().write({'benefits_ids': [(4, 0, benefits.id)]})

        if kwargs.get('job_requirements'):
            vals = {
                'name': kwargs.get('job_requirements'),
                'job_requirement_id': int(kwargs.get('job_id')),
            }
            requirement = request.env['hr.job.requirement'].sudo() \
                .create(vals)
            if requirement:
                job.sudo().write(
                    {'job_requirement_ids': [(4, 0, requirement.id)]})

        if kwargs.get('job_location'):
            vals = {
                'name': kwargs.get('job_location'),
                'job_location_id': int(kwargs.get('job_id')),
            }
            location = request.env['hr.job.location'].sudo().create(vals)
            if location:
                job.sudo().write({'location_ids': [(4, 0, location.id)]})
        return request.render("job_portal.job_review_submit", {'job': job})
