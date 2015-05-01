from unittest import TestCase
from canvas_course_site_wizard.controller import is_bulk_job_in_progress
from canvas_course_site_wizard.models import BulkJob
import datetime

class TestControllerIsBulkJobInProgress(TestCase):
    """
    Tests for the method is_bulk_job_in_progress.
    """

    def setUp(self):
        self.template_id = 123456
        self.term_id = 4545
        self.bulk_job_id = 999
        self.created_at = datetime.datetime.now()
        self.updated_at = datetime.datetime.now()
        BulkJob.objects.create(bulk_job_id=self.bulk_job_id, sis_term_id=self.term_id, status=BulkJob.STATUS_NOTIFICATION_SUCCESSFUL, created_at=self.created_at, updated_at=self.updated_at)
        BulkJob.objects.create(bulk_job_id=self.bulk_job_id, sis_term_id=self.term_id, status=BulkJob.STATUS_NOTIFICATION_FAILED, created_at=self.created_at, updated_at=self.updated_at)
        BulkJob.objects.create(bulk_job_id=self.bulk_job_id, sis_term_id=self.term_id, status=BulkJob.STATUS_FINALIZING, created_at=self.created_at, updated_at=self.updated_at)
        BulkJob.objects.create(bulk_job_id=self.bulk_job_id, sis_term_id=self.term_id, status=BulkJob.STATUS_PENDING, created_at=self.created_at, updated_at=self.updated_at)
        BulkJob.objects.create(bulk_job_id=self.bulk_job_id, sis_term_id=self.term_id, status=BulkJob.STATUS_SETUP, created_at=self.created_at, updated_at=self.updated_at)


    def test_is_bulk_job_in_progress_when_true(self):
        """
        Tests whether is_bulk_job_in_progress returns true when a job is in progress for the term_id.
        """
        result = is_bulk_job_in_progress(self.term_id)
        self.assertTrue(result)

    def test_is_bulk_job_in_progress_when_false(self):
        """
        Tests whether is_bulk_job_in_progress returns false when no jobs are in progress for the term_id.
        """
        result = is_bulk_job_in_progress(1234)
        self.assertFalse(result)
