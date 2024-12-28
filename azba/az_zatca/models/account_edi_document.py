# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
from odoo.exceptions import UserError

from psycopg2 import OperationalError
import base64
import logging
from datetime import datetime, timedelta
import pytz

_logger = logging.getLogger(__name__)

DEFAULT_BLOCKING_LEVEL = 'error'


class AccountEdiDocument(models.Model):
    _inherit = 'account.edi.document'

    def _process_documents_web_services(self, job_count=None, with_commit=True):
        ''' Post and cancel all the documents that need a web service.
        For ZATCA compliance, documents with moves created less than 24 hours ago are filtered out
        to ensure proper processing time and avoid premature submissions.

        :param job_count:   The maximum number of jobs to process if specified.
        :param with_commit: Flag indicating a commit should be made between each job.
        :return:            The number of remaining jobs to process after ZATCA filtering and processing.
        '''
        all_jobs = self.filtered(lambda d: d.edi_format_id._needs_web_services())._prepare_jobs()
        
        # ============== START OF ZATCA FILTERING ==============
        # Filter out moves that are less than 24 hours old
        filtered_jobs = []
        for documents, doc_type in all_jobs:
            filtered_documents = documents.filtered(lambda d: 
                d.move_id.create_date and 
                (datetime.now(pytz.UTC) - d.move_id.create_date) >= timedelta(hours=24)
            )
            if filtered_documents:
                filtered_jobs.append((filtered_documents, doc_type))
        
        all_jobs = filtered_jobs
        # ============== END OF ZATCA FILTERING ==============
        
        jobs_to_process = all_jobs[0:job_count] if job_count else all_jobs

        for documents, doc_type in jobs_to_process:
            move_to_lock = documents.move_id
            attachments_potential_unlink = documents.attachment_id.filtered(lambda a: not a.res_model and not a.res_id)
            try:
                with self.env.cr.savepoint(flush=False):
                    self._cr.execute('SELECT * FROM account_edi_document WHERE id IN %s FOR UPDATE NOWAIT', [tuple(documents.ids)])
                    self._cr.execute('SELECT * FROM account_move WHERE id IN %s FOR UPDATE NOWAIT', [tuple(move_to_lock.ids)])

                    # Locks the attachments that might be unlinked
                    if attachments_potential_unlink:
                        self._cr.execute('SELECT * FROM ir_attachment WHERE id IN %s FOR UPDATE NOWAIT', [tuple(attachments_potential_unlink.ids)])

            except OperationalError as e:
                if e.pgcode == '55P03':
                    _logger.debug('Another transaction already locked documents rows. Cannot process documents.')
                    if not with_commit:
                        raise UserError(_('This document is being sent by another process already. '))
                    continue
                else:
                    raise e
            self._process_job(documents, doc_type)
            if with_commit and len(jobs_to_process) > 1:
                self.env.cr.commit()

        return len(all_jobs) - len(jobs_to_process)
