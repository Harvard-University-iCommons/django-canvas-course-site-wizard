"""
Process the Content Migration jobs in the CanvasContentMigrationJob table.
    To invoke this Command type "python manage.py process_async_jobs"
"""
from django.core.management.base import NoArgsCommand
from django.conf import settings
from django.db.models import Q
from canvas_course_site_wizard.models import CanvasContentMigrationJob
from canvas_sdk.methods.progress import query_progress
from icommons_common.canvas_utils import SessionInactivityExpirationRC
import logging

SDK_CONTEXT = SessionInactivityExpirationRC(**settings.CANVAS_SDK_SETTINGS)

logger = logging.getLogger(__name__)

class Command(NoArgsCommand):
    """
    Process the Content Migration jobs in the CanvasContentMigrationJob table.
        To invoke this Command type "python manage.py process_async_jobs"
    """
    help = "Process the Content Migration jobs in the CanvasContentMigrationJob table"

    def handle_noargs(self, **options):
        """
        select all the active job in the CanvasContentMigrationJob table and check
        the status using the canvas_sdk.progress method
        """
        jobs = CanvasContentMigrationJob.objects.filter(Q(workflow_state='queued') | Q(workflow_state='running'))

        for job in jobs:
            try: 
                """
                TODO - it turns out we only really need the job_id of the content migration 
                no the whole url since we are using the canvas_sdk to cehck the value. We should
                update this in the database and the setting method. In the meantime just parse out
                the job_id from the url.
                """
                job_id = job.status_url.rsplit('/', 1)[1]
                job_start_message = 'processing job_id %s for course with sis_course_id %s' % (job_id, job.sis_course_id)
                logger.info(job_start_message)
                response = query_progress(SDK_CONTEXT, job_id)
                progress_response = response.json()
                if 'workflow_state' in progress_response:
                    workflow_state = progress_response.get('workflow_state')
                    if workflow_state == 'queued':
                        """
                        if the workflow_state is 'queued' the job has not been started on Canvas.
                        log that we checked
                        """
                        message = 'content migration queued for course with sis_course_id %s' % job.sis_course_id
                        logger.info(message)
                    elif workflow_state == 'running':
                        """
                        if the workflow_state is 'running' the job has started but is not complete yet.
                        Log that we checked
                        """
                        message = 'content migration running for course with sis_course_id %s' % job.sis_course_id
                        logger.info(message)
                    elif workflow_state == 'failed':
                        """
                        TODO:
                            1) what happens on failure?
                        """
                        message = 'content migration failed for course with sis_course_id %s' % job.sis_course_id
                        logger.info(message)
                    elif workflow_state == 'completed':
                        """
                        TODO: 
                            1) set sync to canvas flag
                            2) set course site as 'official'
                            3) add the instructor to the course
                        """
                        message = 'content migration complete for course with sis_course_id %s' % job.sis_course_id
                        logger.info(message)
                    else:
                        """
                        we got a workflow_state value back from canvas that does not
                        match one of the exptected values
                        """
                        message = 'content migration unrecognized workflow_state (%s) for course: %s' % (workflow_state, job.sis_course_id)
                        logger.info(message)
                else:
                    message = 'workflow_state missing from response in job_id %s for course %s' % (job_id, job.sis_course_id)
                    logger.error(message)
            except Exception:
                message = 'An exception occured processing job %s for course with sis_course_id %s' % (job_id, job.sis_course_id)
                logger.exception(message)   
            
