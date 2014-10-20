"""
Process the Content Migration jobs in the CanvasContentMigrationJob table
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
    Process the Content Migration jobs in the CanvasContentMigrationJob table
    """
    help = "Process the Content Migration jobs in the CanvasContentMigrationJob table"

    def check_workflow_type(self, workflow_state):
        """
        check that the workflow_state we got back from canvas matches 
        the expected values: 'queued', 'running', 'failed', 'completed'
        """
        workflow_types = ('queued', 'running', 'failed', 'completed')
        return workflow_state in workflow_types

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
                    workflow_state = progress_response['workflow_state']
                    if workflow_state == 'queued':
                        """
                        if the workflow_state is 'queued' the job has not been started on Canvas.
                        log that we checked
                        """
                        logger.info('content migration queued for course with sis_course_id %s' % job.sis_course_id)
                    elif workflow_state == 'running':
                        """
                        if the workflow_state is 'running' the job has started but is not complete yet.
                        Log that we checked
                        """
                        logger.info('content migration running for course with sis_course_id %s' % job.sis_course_id)
                    elif workflow_state == 'failed':
                        """
                        TODO:
                            1) what happens on failure?
                        """
                        logger.info('content migration failed for course with sis_course_id %s' % job.sis_course_id)
                    elif workflow_state == 'completed':
                        """
                        TODO: 
                            1) set sync to canvas flag
                            2) set course site as 'official'
                            3) add the instructor to the course
                        """
                        logger.info('content migration complete for course with sis_course_id %s' % job.sis_course_id)
                    else:
                        """
                        we got a workflow_state value back from canvas that does not
                        match one of the exptected values
                        """
                        logger.info('content migration unrecognized workflow_state (%s) for course: %s' % (workflow_state, job.sis_course_id))
                    
                else:
                    logger.error('workflow_state missing from response!')
            except Exception:
                message = 'An exception occured processing job %s for course with sis_course_id %s' % (5, job.sis_course_id)
                logger.exception(message)   
            
