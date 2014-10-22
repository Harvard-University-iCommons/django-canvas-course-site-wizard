from unittest import TestCase
from mock import patch
from canvas_course_site_wizard.controller import enroll_creator_in_new_course
from canvas_course_site_wizard.exceptions import NoCanvasUserToEnroll, TooManyMatchingUsersToEnroll


class EnrollCreateInNewCourseTest(TestCase):

    def setUp(self):
        self.sis_course_id = '123456'
        self.account_id = 123
        self.sis_user_id = 'sis-test-user'
        self.course = {
            'id': 1234,
            'account_id': self.account_id,
            'sis_course_id': self.sis_course_id
            }

    @patch('canvas_course_site_wizard.controller.enroll_user_sections')
    @patch('canvas_course_site_wizard.controller.list_users_in_account')
    def test_user_successful_enrollment(self, list_users_mock, enroll_user_mock):
        """
        Test that SDK calls to user and enrollments receive expected values and that
        enroll_creator_in_new_course() returns results of enrollment call
        """
        expected_return_values = {
            'enrollment_state': 'active',
            'type': 'TeacherEnrollment',
            'sis_course_id': self.sis_course_id,
            'sis_section_id': self.sis_course_id
        }
        list_users_mock.return_value.json.return_value = [{'sis_user_id': self.sis_user_id}]
        enroll_user_mock.return_value.json.return_value = expected_return_values
        result = enroll_creator_in_new_course(self.course, self.sis_user_id)
        self.assertTrue(list_users_mock.called)
        self.assertTrue(enroll_user_mock.called)
        self.assertDictContainsSubset(expected_return_values, result, "result contains: %s" % result)

    @patch('canvas_course_site_wizard.controller.enroll_user_sections')
    @patch('canvas_course_site_wizard.controller.list_users_in_account')
    def test_no_matching_users(self, list_users_mock, enroll_user_mock):
        """
        Test that enrollment is not attempted if user does not exist in Canvas and that error is passed back to caller
        """
        list_users_mock.return_value.json.return_value = []
        with self.assertRaises(NoCanvasUserToEnroll):
            result = enroll_creator_in_new_course(self.course, self.sis_user_id)
        self.assertTrue(list_users_mock.called)
        self.assertFalse(enroll_user_mock.called)

    @patch('canvas_course_site_wizard.controller.enroll_user_sections')
    @patch('canvas_course_site_wizard.controller.list_users_in_account')
    def test_multiple_matching_users(self, list_users_mock, enroll_user_mock):
        """
        Test that enrollment is not attempted if there is more than one user in Canvas matching
        the SIS user ID provided, and that error is passed back to caller
        """
        list_users_mock.return_value.json.return_value = [{'sis_user_id': self.sis_user_id}, {'sis_user_id': 'match_2'}]
        with self.assertRaises(TooManyMatchingUsersToEnroll):
            result = enroll_creator_in_new_course(self.course, self.sis_user_id)
        self.assertTrue(list_users_mock.called)
        self.assertFalse(enroll_user_mock.called)