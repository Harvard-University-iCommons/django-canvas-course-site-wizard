from unittest import TestCase
from mock import patch, call, ANY, DEFAULT
from canvas_course_site_wizard.controller import bulk_create_courses
from canvas_course_site_wizard.exceptions import NoTemplateExistsForSchool, CanvasCourseAlreadyExistsError
from django.core.exceptions import ObjectDoesNotExist


@patch.multiple('canvas_course_site_wizard.controller', get_course_data=DEFAULT, create_canvas_course=DEFAULT, start_course_template_copy=DEFAULT, finalize_new_canvas_course=DEFAULT)
class BulkCreateCoursesTest(TestCase):
    longMessage = True

    def setUp(self):
        self.user_id = '12345678'
        self.bulk_job_id = 12345
        self.school_code = 'colgsas'
        self.courses = [123, 456, 789, 1011, 1012, 1013, 1014, 1015]
        self.course_data_calls = []
        self.create_course_calls = []
        self.finalize_calls = []
        self.template_copy_calls = []
        for course in self.courses:
            self.create_course_calls.append(call(course, self.user_id, bulk_job_id=self.bulk_job_id))
            self.course_data_calls.append(call(course))
            self.finalize_calls.append(call(ANY, course, 'sis_user_id:%s' % self.user_id, bulk_job_id=self.bulk_job_id))
            self.template_copy_calls.append(call(ANY, ANY, self.user_id, bulk_job_id=self.bulk_job_id))


    def test_bulk_create_courses_get_course_data(self, get_course_data, create_canvas_course, start_course_template_copy, finalize_new_canvas_course):
        """
        Test that get course data is called with the correct params for each course
        """
        errors, messages = bulk_create_courses(self.courses, self.user_id, self.bulk_job_id)
        get_course_data.assert_has_calls(self.course_data_calls, any_order=True)



    def test_bulk_create_courses_create_canvas_course(self, get_course_data, create_canvas_course, start_course_template_copy, finalize_new_canvas_course):
        """
        Test that create canvas course is called with the correct params for each course
        """
        errors, messages = bulk_create_courses(self.courses, self.user_id, self.bulk_job_id)
        create_canvas_course.assert_has_calls(self.create_course_calls, any_order=True)


    def test_bulk_create_courses_start_course_template_copy(self, get_course_data, create_canvas_course, start_course_template_copy, finalize_new_canvas_course):
        """
        Test that start course template copy is called with the correct params for each course
        """
        errors, messages = bulk_create_courses(self.courses, self.user_id, self.bulk_job_id)
        start_course_template_copy.assert_has_calls(self.template_copy_calls, any_order=True)



    def test_bulk_create_courses_finalize_new_canvas_course(self, get_course_data, create_canvas_course, start_course_template_copy, finalize_new_canvas_course):
        """
        Test that finalize new canvas course is called with the correct params for each course
        """
        start_course_template_copy.side_effect = NoTemplateExistsForSchool(self.school_code)
        errors, messages = bulk_create_courses(self.courses, self.user_id, self.bulk_job_id)
        finalize_new_canvas_course.assert_has_calls(self.finalize_calls, any_order=True)

    @patch('canvas_course_site_wizard.controller.logger.error')
    def test_bulk_create_courses_get_course_data_with_error(self, mock_logger, get_course_data, create_canvas_course, start_course_template_copy, finalize_new_canvas_course ):
        """
        Test that logger is called when get course data throws and exception
        """
        get_course_data.side_effect = ObjectDoesNotExist()
        errors, messages = bulk_create_courses(self.courses, self.user_id, self.bulk_job_id)
        mock_logger.assert_called_with(ANY)
        mock_logger.assertEqual(mock_logger.call_count, len(self.courses))

    @patch('canvas_course_site_wizard.controller.logger.error')
    def test_bulk_create_courses_create_new_course_error(self, mock_logger, get_course_data, create_canvas_course, start_course_template_copy, finalize_new_canvas_course ):
        """
        Test that logger is called when create course throws and exception
        """
        create_canvas_course.side_effect = CanvasCourseAlreadyExistsError(msg_details=self.school_code)
        errors, messages = bulk_create_courses(self.courses, self.user_id, self.bulk_job_id)
        mock_logger.assert_called_with(ANY)
        mock_logger.assertEqual(mock_logger.call_count, len(self.courses)-1)