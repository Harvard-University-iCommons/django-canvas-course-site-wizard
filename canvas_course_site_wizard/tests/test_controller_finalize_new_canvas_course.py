from unittest import TestCase
from mock import patch
from canvas_course_site_wizard.controller import finalize_new_canvas_course
from canvas_course_site_wizard.exceptions import NoCanvasUserToEnroll


@patch('canvas_course_site_wizard.controller.enroll_creator_in_new_course')
class FinalizeNewCanvasCourseTest(TestCase):

    def setUp(self):
        self.sis_course_id = '123456'
        self.account_id = 123
        self.sis_user_id = 'sis-test-user'
        self.course = {
            'id': 1234,
            'account_id': self.account_id,
            'sis_course_id': self.sis_course_id
        }

    def test_successful_finalization(self, enroll_creator_mock):
        """
        Test that all steps in finalize course are called in order with the appropriate arguments
        """
        finalize_new_canvas_course(self.course, self.sis_user_id)
        enroll_creator_mock.assert_called_once_with(self.course, self.sis_user_id)

    @patch('canvas_course_site_wizard.controller.logger.error')
    def test_log_find_canvas_user_errors(self, enroll_creator_mock, logger_mock):
        """
        Test that errors identifying the creator in Canvas are logged
        """
        enroll_creator_mock.side_effect = NoCanvasUserToEnroll(self.sis_user_id)
        finalize_new_canvas_course(self.course, self.sis_user_id)
        logger_mock.assert_called()
