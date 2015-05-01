from django.test import TestCase
from canvas_course_site_wizard.controller import get_bulk_jobs_for_term
from canvas_course_site_wizard.models import BulkJob
import datetime

class TestControllerGetBulkJobsForTerm(TestCase):
    """
    Tests for the method get_bulk_jobs_for_term.
    """

    def setUp(self):
        self.template_id = 123456
        self.term_id = 4700
        self.bulk_job_id = 999
        self.created_at = datetime.datetime.now()
        self.updated_at = datetime.datetime.now()
        BulkJob.objects.create(bulk_job_id=self.bulk_job_id, sis_term_id=self.term_id, status=BulkJob.STATUS_NOTIFICATION_SUCCESSFUL, created_at=self.created_at, updated_at=self.updated_at)
        BulkJob.objects.create(bulk_job_id=self.bulk_job_id, sis_term_id=self.term_id, status=BulkJob.STATUS_NOTIFICATION_FAILED, created_at=self.created_at, updated_at=self.updated_at)
        BulkJob.objects.create(bulk_job_id=self.bulk_job_id, sis_term_id=self.term_id, status=BulkJob.STATUS_FINALIZING, created_at=self.created_at, updated_at=self.updated_at)
        BulkJob.objects.create(bulk_job_id=self.bulk_job_id, sis_term_id=self.term_id, status=BulkJob.STATUS_PENDING, created_at=self.created_at, updated_at=self.updated_at)
        BulkJob.objects.create(bulk_job_id=self.bulk_job_id, sis_term_id=self.term_id, status=BulkJob.STATUS_SETUP, created_at=self.created_at, updated_at=self.updated_at)


    def test_get_bulk_jobs_for_term_when_term_has_data(self):
        """
        Tests whether get_bulk_jobs_for_term returns all the jobs for the term provided.
        """
        data = [
            '<BulkJob: (BulkJob ID=5: sis_term_id=4700)>',
            '<BulkJob: (BulkJob ID=2: sis_term_id=4700)>',
            '<BulkJob: (BulkJob ID=4: sis_term_id=4700)>',
            '<BulkJob: (BulkJob ID=1: sis_term_id=4700)>',
            '<BulkJob: (BulkJob ID=3: sis_term_id=4700)>',
        ]
        result = get_bulk_jobs_for_term(self.term_id)
        self.assertQuerysetEqual(result, data, ordered=False)

    def test_get_bulk_jobs_for_term_when_term_has_no_data(self):
        """
        Tests whether get_bulk_jobs_for_term returns no jobs for a different term that doens't have jobs.
        """
        result = get_bulk_jobs_for_term(1234)
        self.assertQuerysetEqual(result, [], ordered=False)
