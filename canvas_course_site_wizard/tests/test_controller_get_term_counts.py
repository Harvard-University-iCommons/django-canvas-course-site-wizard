from unittest import TestCase
from mock import patch
from canvas_course_site_wizard.controller import get_term_course_counts
from setup_bulk_jobs import create_jobs

class TestControllerGetTermCourseCounts(TestCase):
    """
    Tests for the method get_term_course_counts.
    """

    def setUp(self):
        self.template_id = 123456
        self.school_id = 'colgsas'
        self.term_id = 4848
        create_jobs(self.school_id, self.term_id)

    @patch('canvas_course_site_wizard.controller.get_courses_for_term')
    def test_get_term_course_counts(self, mock_course_call):
        """
        Tests whether get_term_course_counts returns the correct result.
        """
        test_data = {
            'total_courses': 25,
            'canvas_courses': 25,
            'isites_courses' : 25,
            'not_created' : 25,
        }
        test_data['external'] = test_data['total_courses'] - test_data['canvas_courses'] - test_data['isites_courses'] - test_data['not_created']
        mock_course_call.return_value = 25
        result = get_term_course_counts(self.term_id)
        self.assertEqual(result, test_data)

