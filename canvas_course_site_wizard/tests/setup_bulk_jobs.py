from canvas_course_site_wizard.models import BulkJob
import datetime

STATUSES = [BulkJob.STATUS_FINALIZING, BulkJob.STATUS_NOTIFICATION_FAILED,
            BulkJob.STATUS_NOTIFICATION_SUCCESSFUL, BulkJob.STATUS_PENDING,
            BulkJob.STATUS_SETUP]

def create_bulk_jobs(term_id, job_id):
    created_at = datetime.datetime.now()
    updated_at = datetime.datetime.now()
    for status in STATUSES:
        BulkJob.objects.create(bulk_job_id=job_id,
                               sis_term_id=term_id,
                               status=status,
                               created_at=created_at,
                               updated_at=updated_at)


