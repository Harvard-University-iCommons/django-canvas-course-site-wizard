from unittest import TestCase
from mock import patch, MagicMock
from canvas_course_site_wizard.models import SISCourseData
from canvas_course_site_wizard.controller import finalize_new_canvas_course


class FinalizeNewCanvasCourseTest(TestCase):

    def setUp(self):
        self.canvas_course_id = '123'
        self.sis_course_id = '123456'
        self.user_id = 999
        self.test_return_value = None

    @patch('canvas_course_site_wizard.controller.get_canvas_course_url')
    @patch('canvas_course_site_wizard.controller.get_course_data')
    @patch('canvas_course_site_wizard.controller.logger')
    @patch('canvas_course_site_wizard.controller.enroll_creator_in_new_course')
    def test_successful_finalization(self, enroll_creator_mock, logger_mock, course_data_mock, url_mock):
        """
        If all finalization steps are successful, there should be no calls to logger.error() and the return value
        should be the new course URL.
        """
        test_url = 'test_url/'
        url_mock.return_value = test_url
        self.test_return_value = finalize_new_canvas_course(self.canvas_course_id, self.sis_course_id, self.user_id)
        self.assert_log_level_calls(logger_mock, 'error', 0)
        self.assertEquals(self.test_return_value, test_url)

    @patch('canvas_course_site_wizard.controller.get_canvas_course_url')
    @patch('canvas_course_site_wizard.controller.get_course_data')
    @patch('canvas_course_site_wizard.controller.logger')
    @patch('canvas_course_site_wizard.controller.enroll_creator_in_new_course')
    def test_enrollment_failure(self, enroll_creator_mock, logger_mock, course_data_mock, url_mock):
        """
        If the automatic enrollment of the course creator fails, we should be logging an error and exiting the
        finalization process without a return value and before proceeding with other steps.
        """
        enroll_creator_mock.side_effect = Exception('Mock exception')
        with self.assertRaises(Exception):
            self.test_return_value = finalize_new_canvas_course(self.canvas_course_id, self.sis_course_id, self.user_id)
        enroll_creator_mock.assert_called_once_with(self.sis_course_id, self.user_id)
        self.assertFalse(course_data_mock.called)
        self.assert_log_level_calls(logger_mock, 'error', 1, regex_to_check=r'Error enrolling course creator')
        self.assertIsNone(self.test_return_value)

    @patch('canvas_course_site_wizard.controller.get_canvas_course_url')
    @patch('canvas_course_site_wizard.controller.get_course_data')
    @patch('canvas_course_site_wizard.controller.logger')
    @patch('canvas_course_site_wizard.controller.enroll_creator_in_new_course')
    def test_course_url_failure(self, enroll_creator_mock, logger_mock, course_data_mock, url_mock):
        """
        If unable to get a Canvas course URL for the new course, we should be logging an error and exiting the
        finalization process without a return value and before proceeding with other steps.
        """
        url_mock.side_effect = Exception('Mock exception')
        with self.assertRaises(Exception):
            self.test_return_value = finalize_new_canvas_course(self.canvas_course_id, self.sis_course_id, self.user_id)
        url_mock.assert_called_once_with(canvas_course_id=self.canvas_course_id)
        self.assertFalse(course_data_mock().set_sync_to_canvas().called)
        self.assert_log_level_calls(logger_mock, 'error', 1, regex_to_check=r'Error marking new course.*official')
        self.assertIsNone(self.test_return_value)

    @patch('canvas_course_site_wizard.controller.get_canvas_course_url')
    @patch('canvas_course_site_wizard.controller.get_course_data')
    @patch('canvas_course_site_wizard.controller.logger')
    @patch('canvas_course_site_wizard.controller.enroll_creator_in_new_course')
    def test_set_official_failure(self, enroll_creator_mock, logger_mock, course_data_mock, url_mock):
        """
        If unable to set the Canvas course as 'official', we should be logging an error and exiting the
        finalization process without a return value and before proceeding with other steps.
        """
        course_data_mock().set_sync_to_canvas().set_official_course_site_url.side_effect = Exception('Mock exception')
        test_url = 'test_url/'
        url_mock.return_value = test_url
        with self.assertRaises(Exception):
            self.test_return_value = finalize_new_canvas_course(self.canvas_course_id, self.sis_course_id, self.user_id)
        url_mock.assert_called_once_with(canvas_course_id=self.canvas_course_id)
        course_data_mock().set_sync_to_canvas().set_official_course_site_url.assert_called_once_with(test_url)
        self.assert_log_level_calls(logger_mock, 'error', 1, regex_to_check=r'Error marking new course.*official')
        self.assertIsNone(self.test_return_value)

    @patch('canvas_course_site_wizard.controller.get_course_data')
    @patch('canvas_course_site_wizard.controller.logger')
    @patch('canvas_course_site_wizard.controller.enroll_creator_in_new_course')
    def test_course_data_failure(self, enroll_creator_mock, logger_mock, course_data_mock):
        """
        If unable to get SIS course data for the course (which we need to mark the Canvas course as official and
        sync enrollment to Canvas), we should be logging an error and exiting the
        finalization process without a return value and before proceeding with other steps.
        """
        course_data_mock.side_effect = Exception('Mock exception')
        with self.assertRaises(Exception):
            self.test_return_value = finalize_new_canvas_course(self.canvas_course_id, self.sis_course_id, self.user_id)
        enroll_creator_mock.assert_called_once_with(self.sis_course_id, self.user_id)
        course_data_mock.assert_called_once_with(self.sis_course_id)
        error_calls = [c[1][0] for c in logger_mock.mock_calls if 'error' in c[0]]
        self.assertEqual(len(error_calls), 1)
        self.assertRegexpMatches(error_calls[0], r'Error setting SIS enrollment')
        self.assertIsNone(self.test_return_value)

    @patch('canvas_course_site_wizard.controller.get_canvas_course_url')
    @patch('canvas_course_site_wizard.controller.get_course_data')
    @patch('canvas_course_site_wizard.controller.logger')
    @patch('canvas_course_site_wizard.controller.enroll_creator_in_new_course')
    def test_sync_failure(self, enroll_creator_mock, logger_mock, course_data_mock, url_mock):
        """
        If unable to set the sync enrollment to Canvas flag for the course we should be logging an error and exiting the
        finalization process without a return value and before proceeding with other steps.
        """
        course_data_mock().set_sync_to_canvas.side_effect = Exception('Mock exception')
        logger_mock().error = MagicMock
        with self.assertRaises(Exception):
            self.test_return_value = finalize_new_canvas_course(self.canvas_course_id, self.sis_course_id, self.user_id)
        self.assertTrue(logger_mock().error.called)
        self.assert_log_level_calls(logger_mock, 'error', 1, regex_to_check=r'Error setting SIS enrollment')
        self.assertTrue(course_data_mock().set_sync_to_canvas.called)
        course_data_mock().set_sync_to_canvas.assert_called_with(SISCourseData.TURN_ON_SYNC_TO_CANVAS)
        self.assertFalse(url_mock.called)
        self.assertIsNone(self.test_return_value)

    def assert_log_level_calls(self, logger_mock, log_level, expected_number_of_calls, regex_to_check=None):
        """
        Utility method for FinalizeNewCanvasCourseTest unit tests to assert that a particular number of log messages
         were output at a particular log level by a mock logger (which must be provided to the utility method).
        :param logger_mock: the Mock object which simulates the real-world logger object for the test target.
        :param log_level: string value equal to 'error', 'debug', 'info', 'warn', etc.
        :param expected_number_of_calls: the method will assert whether this variable equals the number of times the
        mock logger was called by the test method up to this point.
        :param regex_to_check: Optional. If this regex (which can be declared as r'regex string to-search for') is
        included, the method will also assert that this message appears in the first call -- intended to be asserted
        when only a single call was expected (i.e. expected_number_of_calls == 1)
        :return: n/a
        :raises: Assertion error if the expected_number_of_calls or optional regex_to_check assertion fails.
        """
        calls = [c[1][0] for c in logger_mock.mock_calls if log_level in c[0]]
        self.assertEqual(len(calls), expected_number_of_calls)
        if regex_to_check is not None:
            self.assertRegexpMatches(calls[0], regex_to_check)
