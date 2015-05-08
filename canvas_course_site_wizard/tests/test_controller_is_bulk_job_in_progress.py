from unittest import TestCase
from canvas_course_site_wizard.controller import is_bulk_job_in_progress
from setup_bulk_jobs import create_bulk_jobs


class TestControllerIsBulkJobInProgress(TestCase):
    """
    Tests for the method is_bulk_job_in_progress.
    """

    def setUp(self):
        self.template_id = 123456
        self.term_id = 4848
        create_bulk_jobs(self.term_id)

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
