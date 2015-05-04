from unittest import TestCase
from mock import patch
from canvas_course_site_wizard.controller import get_term_course_counts
from setup_bulk_jobs import create_bulk_jobs

class TestControllerGetTermCourseCounts(TestCase):
    """
    Tests for the method get_term_course_counts.
    """

    def setUp(self):
        self.template_id = 123456
        self.term_id = 4848
        self.bulk_job_id = 901
        create_bulk_jobs(self.term_id, self.bulk_job_id)

    @patch('canvas_course_site_wizard.controller.get_courses_for_term')
    def test_get_term_course_counts(self, mock_course_call):
        """
        Tests whether get_term_course_counts returns the correct result.
        """
        test_data = {
            'canvas_courses': 99,
            'not_in_canvas': 0,
            'total_courses': 99
        }
        mock_course_call.return_value = 99
        result = get_term_course_counts(self.term_id)
        self.assertEqual(result, test_data)

