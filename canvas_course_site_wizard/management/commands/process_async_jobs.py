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
                workflow_state = progress_response['workflow_state']
                
                if workflow_state == 'completed':
                    """
                    TODO: 
                        1) update workflow_state in table for job_id
                        2) set sync to canvas flag
                        3) set course site as 'official'
                        4) add the instructor to the course
                    """
                    message = 'content migration complete for course with sis_course_id %s' % job.sis_course_id
                    logger.info(message)

                elif workflow_state == 'failed':
                    """
                    TODO:
                        1) update workflow_state in table for job_id
                    """
                    message = 'content migration failed for course with sis_course_id %s' % job.sis_course_id
                    logger.info(message)
                else:
                    """
                    if the workflow_state is 'queued' or 'running' the job 
                    is not complete and a failure has not occured on Canvas.
                    log that we checked
                    TODO:
                        1) update workflow state in table for job_id
                    """
                    message = 'content migration queued for course with sis_course_id %s' % job.sis_course_id
                    logger.info(message)

            except KeyError:
                message = 'the workflow_state parameter was not present in the canvas response for job %s' % job_id
                logger.exception(message) 
    
            except Exception:
                message = 'An exception occured processing job %s for course with sis_course_id %s' % (job_id, job.sis_course_id)
                logger.exception(message)   
            
