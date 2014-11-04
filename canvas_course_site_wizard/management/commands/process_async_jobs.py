"""
Process the Content Migration jobs in the CanvasContentMigrationJob table.
    To invoke this Command type "python manage.py process_async_jobs"
"""
from django.core.management.base import NoArgsCommand
from django.conf import settings
from django.db.models import Q
from canvas_course_site_wizard.controller import (get_canvas_user_profile, send_email_helper, send_failure_email)
from canvas_course_site_wizard.models import CanvasContentMigrationJob
from canvas_course_site_wizard.controller import finalize_new_canvas_course
from canvas_sdk import client
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
                
                job_start_message = '\nProcessing course with sis_course_id %s' % (job.sis_course_id)
                logger.info(job_start_message)
                user_profile = None
                response = client.get(SDK_CONTEXT, job.status_url)
                progress_response = response.json()
                workflow_state = progress_response['workflow_state']
                
                if workflow_state == 'completed':
                    logger.info('content migration complete for course with sis_course_id %s' % job.sis_course_id)
                    # Update the Job table with the completed state immediately to indicate that the template
                    # migration was successful
                    job.workflow_state = 'completed'
                    job.save(update_fields=['workflow_state'])

                    logger.debug('Workflow state updated, starting finalization process...')
                    canvas_course_url = finalize_new_canvas_course(job.canvas_course_id, job.sis_course_id,
                                                                   'sis_user_id:%s' % job.created_by_user_id)

                    #Once finalized successfully, only the initiator needs to be emailed
                    user_profile = get_canvas_user_profile(job.created_by_user_id)
                    to_address =[]
                    to_address.append(user_profile['primary_email'])
                    success_msg = settings.CANVAS_EMAIL_NOTIFICATION['course_migration_success_body']
                    logger.debug("notifying  success via email:  to_addr=%s and adding course url =%s" % (to_address,canvas_course_url))

                    #add the course url to the  message
                    complete_msg = success_msg.format(canvas_course_url)
                    send_email_helper(settings.CANVAS_EMAIL_NOTIFICATION['course_migration_success_subject'],
                            complete_msg,to_address)

                elif workflow_state == 'failed':
                    logger.info('content migration failed for course with sis_course_id %s' % job.sis_course_id)

                    # Update the Job table with the new state
                    job.workflow_state = 'failed'
                    job.save(update_fields=['workflow_state'])
                    #send email to notify of failure
                    user_profile = get_canvas_user_profile(job.created_by_user_id)
                    to_address =[]
                    send_failure_email(user_profile['primary_email'], job.sis_course_id)

                else:
                    """
                    if the workflow_state is 'queued' or 'running' the job 
                    is not complete and a failure has not occured on Canvas.
                    log that we checked
                    Note: we won't need to update the DB as we will record only the completin or failure in the job table
                    """
                    message = 'content migration state is %s for course with sis_course_id %s' % (workflow_state, job.sis_course_id)
                    logger.info(message)

            except KeyError as e:
                logger.exception(e)
            except Exception as e:
                logger.exception(" There was a problem in processing the job for canvas course  sis_course_id=%s, exception=%s" % (job.sis_course_id,e))
                try :
                    #if failure happened before user profile was fetched, get the user profile to retrieve email, else reuse teh user_profile info
                    if user_profile == None:
                        user_profile = get_canvas_user_profile(job.created_by_user_id)

                    send_failure_email(user_profile['primary_email'], job.sis_course_id)
                except Exception as e:
                    #If exception occurs while sending failure email, log it
                    logger.exception(" There was a problem in sending the failure notification  email to initiator and support staff for sis_course_id=%s, exception=%s" % (job.sis_course_id,e))

        

