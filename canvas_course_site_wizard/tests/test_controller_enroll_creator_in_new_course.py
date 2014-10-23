from unittest import TestCase
from mock import patch, DEFAULT, ANY
from canvas_course_site_wizard.controller import enroll_creator_in_new_course
from canvas_course_site_wizard.exceptions import NoCanvasUserToEnroll


@patch.multiple('canvas_course_site_wizard.controller', get_user_profile=DEFAULT, enroll_user_sections=DEFAULT)
class EnrollCreateInNewCourseTest(TestCase):

    def setUp(self):
        self.sis_course_id = '123456'
        self.account_id = 123
        self.sis_user_id = 'sis-test-user'
        self.canvas_user_id = '5555'
        self.course = {
            'id': 1234,
            'account_id': self.account_id,
            'sis_course_id': self.sis_course_id
        }

    def test_user_successful_enrollment(self, get_user_profile, enroll_user_sections):
        """
        Test that SDK calls to user and enrollments receive expected values and that
        enroll_creator_in_new_course() returns results of enrollment call
        """
        enroll_user_sections_expected_return_values = {
            'enrollment_state': 'active',
            'type': 'TeacherEnrollment',
            'sis_course_id': self.sis_course_id,
            'sis_section_id': self.sis_course_id
        }
        get_user_profile.return_value.status_code = 200
        get_user_profile.return_value.json.return_value = {'id': self.canvas_user_id}
        enroll_user_sections.return_value.json.return_value = enroll_user_sections_expected_return_values
        result = enroll_creator_in_new_course(self.course, self.sis_user_id)
        get_user_profile.assert_called_with(request_ctx=ANY, user_id='sis_user_id:%s' % self.sis_user_id)
        enroll_user_sections.assert_called_with(request_ctx=ANY, section_id='sis_section_id:%s' % self.sis_course_id,
                                                enrollment_user_id=self.canvas_user_id,
                                                enrollment_type='TeacherEnrollment',
                                                enrollment_enrollment_state='active')
        self.assertDictContainsSubset(enroll_user_sections_expected_return_values, result,
                                      "result contains: %s" % result)

    def test_no_user_to_enroll(self, get_user_profile, enroll_user_sections):
        """
        Test that error is passed back to caller if user does not exist in Canvas
        """
        get_user_profile.return_value.status_code.return_value = 404
        with self.assertRaises(NoCanvasUserToEnroll):
            result = enroll_creator_in_new_course(self.course, self.sis_user_id)
        self.assertTrue(get_user_profile.called)
