from canvas_course_site_wizard.models import BulkCanvasCourseCreationJob
import datetime

STATUSES = [BulkCanvasCourseCreationJob.STATUS_FINALIZING, BulkCanvasCourseCreationJob.STATUS_NOTIFICATION_FAILED,
            BulkCanvasCourseCreationJob.STATUS_NOTIFICATION_SUCCESSFUL, BulkCanvasCourseCreationJob.STATUS_PENDING,
            BulkCanvasCourseCreationJob.STATUS_SETUP]

def create_bulk_jobs(term_id, job_id):
    created_at = datetime.datetime.now()
    updated_at = datetime.datetime.now()
    for status in STATUSES:
        BulkCanvasCourseCreationJob.objects.create(bulk_job_id=job_id,
                               sis_term_id=term_id,
                               status=status,
                               created_at=created_at,
                               updated_at=updated_at)


