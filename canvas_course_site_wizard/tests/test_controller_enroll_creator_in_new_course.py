from unittest import TestCase
from mock import patch, DEFAULT, ANY
from canvas_course_site_wizard.controller import enroll_creator_in_new_course
from canvas_course_site_wizard.exceptions import NoCanvasUserToEnroll


@patch.multiple('canvas_course_site_wizard.controller', get_user_profile=DEFAULT, enroll_user_sections=DEFAULT)
class EnrollCreateInNewCourseTest(TestCase):

    def setUp(self):
        self.sis_course_id = '123456'
        self.sis_user_id = 'sis-test-user'
        self.canvas_user_id = '5555'
        self.user_id = None

    def test_sis_user_id(self, get_user_profile, enroll_user_sections):
        """ Successful enrollment using SIS user ID """
        self.initialize_test(get_user_profile, enroll_user_sections)
        self.user_id = 'sis_user_id:%s' % self.sis_user_id
        test_result = enroll_creator_in_new_course(self.sis_course_id, self.user_id)
        self.verify_test(get_user_profile, enroll_user_sections)

    def test_canvas_user_id(self, get_user_profile, enroll_user_sections):
        """ Successful enrollment using Canvas user ID """
        self.initialize_test(get_user_profile, enroll_user_sections)
        self.user_id = self.canvas_user_id
        test_result = enroll_creator_in_new_course(self.sis_course_id, self.user_id)
        self.verify_test(get_user_profile, enroll_user_sections)

    def test_canvas_user_not_found(self, get_user_profile, enroll_user_sections):
        """ Fail before enrollment attempt if user does not exist in Canvas """
        get_user_profile.return_value.status_code.return_value = 404
        bad_user_id = '    '  # mocking a bad user ID
        with self.assertRaises(NoCanvasUserToEnroll):
            result = enroll_creator_in_new_course(self.sis_course_id, bad_user_id)
        get_user_profile.assert_called_with(request_ctx=ANY, user_id=bad_user_id)

    def initialize_test(self, get_user_profile_mock, enroll_user_sections_mock):
        get_user_profile_mock.return_value.status_code = 200
        get_user_profile_mock.return_value.json.return_value = {'id': self.canvas_user_id,
                                                                'sis_user_id': self.sis_user_id}

    def verify_test(self, get_user_profile_mock, enroll_user_sections_mock):
        get_user_profile_mock.assert_called_with(request_ctx=ANY, user_id=self.user_id)
        enroll_user_sections_mock.assert_called_with(request_ctx=ANY,
                                                     section_id='sis_section_id:%s' % self.sis_course_id,
                                                     enrollment_user_id=self.canvas_user_id,
                                                     enrollment_type='TeacherEnrollment',
                                                     enrollment_enrollment_state='active')
