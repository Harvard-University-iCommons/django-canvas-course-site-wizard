from django.test import TestCase
from canvas_course_site_wizard.controller import get_bulk_jobs_for_term
from setup_bulk_jobs import create_jobs


class TestControllerGetBulkJobsForTerm(TestCase):
    """
    Tests for the method get_bulk_jobs_for_term.
    """

    def setUp(self):
        self.template_id = 123456
        self.school_id = 'colgsas'
        self.term_id = 4700
        create_jobs(self.school_id, self.term_id)

    def test_get_bulk_jobs_for_term_when_term_has_data(self):
        """
        Tests whether get_bulk_jobs_for_term returns all the jobs for the term provided.
        """
        data = [
            '<BulkCanvasCourseCreationJob: (BulkJob ID=5: sis_term_id=4700)>',
            '<BulkCanvasCourseCreationJob: (BulkJob ID=2: sis_term_id=4700)>',
            '<BulkCanvasCourseCreationJob: (BulkJob ID=4: sis_term_id=4700)>',
            '<BulkCanvasCourseCreationJob: (BulkJob ID=1: sis_term_id=4700)>',
            '<BulkCanvasCourseCreationJob: (BulkJob ID=3: sis_term_id=4700)>',
        ]
        result = get_bulk_jobs_for_term(self.term_id)
        self.assertQuerysetEqual(result, data, ordered=False)

    def test_get_bulk_jobs_for_term_when_term_has_no_data(self):
        """
        Tests whether get_bulk_jobs_for_term returns no jobs for a different term that doens't have jobs.
        """
        result = get_bulk_jobs_for_term(1234)
        self.assertQuerysetEqual(result, [], ordered=False)
