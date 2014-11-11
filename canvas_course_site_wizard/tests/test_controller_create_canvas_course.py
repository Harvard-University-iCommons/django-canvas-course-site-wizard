from unittest import TestCase
from mock import patch, DEFAULT, MagicMock
from icommons_ui.exceptions import RenderableException
from django.core.exceptions import ObjectDoesNotExist
from requests.exceptions import HTTPError
import canvas_course_site_wizard.controller


@patch.multiple('canvas_course_site_wizard.controller',
                get_course_data=DEFAULT, create_course_section=DEFAULT, create_new_course=DEFAULT)
class CreateCanvasCourseTest(TestCase):
    longMessage = True

    def setUp(self):
        self.sis_course_id = "305841"

    def get_mock_of_get_course_data(self):
        # mock the properties
        course_model_mock = MagicMock(sis_account_id="school:gse",
                                      course_code="GSE",
                                      course_name="GSE test course",
                                      sis_term_id="gse term")
        # mock the methods
        course_model_mock.primary_section_name.return_value = "Primary section"
        return course_model_mock

    # ------------------------------------------------------
    # Tests for create_canvas_course()
    # ------------------------------------------------------

    @patch('canvas_course_site_wizard.controller.create_canvas_course')
    def test_create_canvas_course_method_called_with_right_params(self, create_canvas_course, get_course_data,
                                                                  create_course_section, create_new_course):
        """
        Test that controller makes create_canvas_course call with expected args
        """
        result = create_canvas_course(self.sis_course_id)
        create_canvas_course.assert_called_with(self.sis_course_id)

    # ------------------------------------------------------
    # Tests for create_canvas_course.get_course_data()
    # ------------------------------------------------------

    def test_get_course_data_method_called_with_right_params(self, get_course_data,
                                                             create_course_section, create_new_course):
        """
        Test that controller method makes a call to get_course_data api with expected args
        """
        canvas_course_site_wizard.controller.create_canvas_course(self.sis_course_id)
        get_course_data.assert_called_with(self.sis_course_id)

    def test_exception_in_get_course_data(self, get_course_data, create_course_section, create_new_course):
        """
        Test that an exception is raised when get_course_data throws an exception
        """
        canvas_course_site_wizard.controller.create_canvas_course(self.sis_course_id)
        get_course_data.side_effect = Exception
        self.assertRaises(Exception, get_course_data, self.sis_course_id)

    def test_object_not_found_exception_in_get_course_data(self, get_course_data,
                                                           create_course_section, create_new_course):
        """
        Test  when get_course_data throws an ObjectDoesNotExist
        Note: Http404 exception is one of the exceptions not visible to the test client. 
        So just checking for ObjectDoesNotExist
        """
        canvas_course_site_wizard.controller.create_canvas_course(self.sis_course_id)
        get_course_data.side_effect = ObjectDoesNotExist
        self.assertRaises(ObjectDoesNotExist, get_course_data, self.sis_course_id)

    @patch('canvas_course_site_wizard.controller.logger')
    def test_object_not_found_exception_in_get_course_data_logs_error(self, log_replacement, get_course_data,
                                                                      create_course_section, create_new_course):
        """
        Test that the logger.error logs error when when get_course_data throws an ObjectDoesNotExist
        """
        get_course_data.side_effect = ObjectDoesNotExist
        with self.assertRaises(RenderableException):
            canvas_course_site_wizard.controller.create_canvas_course(self.sis_course_id)
        self.assertTrue(log_replacement.error.called)

    # ------------------------------------------------------
    # Tests for create_canvas_course.create_course_section()
    # ------------------------------------------------------

    @patch('canvas_course_site_wizard.controller.SDK_CONTEXT')
    def test_create_new_course_method_is_called_with_proper_arguments(self, SDK_CONTEXT, get_course_data,
                                                                      create_course_section, create_new_course):
        """
        Test to assert that create_new_course method is called by create_canvas_course controller method
        with appropriate arguments (collapses a bunch of individual parameter tests)
        """
        course_model_mock = self.get_mock_of_get_course_data()
        get_course_data.return_value = course_model_mock
        canvas_course_site_wizard.controller.create_canvas_course(self.sis_course_id)
        sis_account_id_argument = 'sis_account_id:' + course_model_mock.sis_account_id
        course_code_argument = course_model_mock.course_code
        course_name_argument = course_model_mock.course_name
        course_term_id_argument = 'sis_term_id:' + course_model_mock.sis_term_id
        course_sis_course_id_argument = self.sis_course_id
        create_new_course.assert_called_with(request_ctx=SDK_CONTEXT, account_id=sis_account_id_argument,
                                             course_name=course_name_argument, course_course_code=course_code_argument,
                                             course_term_id=course_term_id_argument,
                                             course_sis_course_id=course_sis_course_id_argument)

    def test_when_create_new_course_method_raises_exception(self, get_course_data,
                                                            create_course_section, create_new_course):
        """
        Test to assert that a RenderableException is raised when the create_new_course method
        throws an exception
        """
        create_new_course.side_effect = Exception
        with self.assertRaises(RenderableException):
            canvas_course_site_wizard.controller.create_canvas_course(self.sis_course_id)

    def test_when_create_new_course_method_raises_httperror(self, get_course_data,
                                                            create_course_section, create_new_course):
        """
        Test to assert that a RenderableException is raised when the create_new_course SDK call
        throws an HTTPError
        """
        create_new_course.side_effect = HTTPError
        with self.assertRaises(RenderableException):
            canvas_course_site_wizard.controller.create_canvas_course(self.sis_course_id)

    # ------------------------------------------------------
    # Tests for create_canvas_course.create_course_section()
    # ------------------------------------------------------

    @patch('canvas_course_site_wizard.controller.SDK_CONTEXT')
    def test_create_course_section_method_is_called(self, SDK_CONTEXT, get_course_data,
                                                    create_course_section, create_new_course):
        """
        Test to assert that create_new_course method is called by create_canvas_course controller method
        """
        course_model_mock = self.get_mock_of_get_course_data()
        get_course_data.return_value = course_model_mock
        mock_canvas_course_id = '12345'
        mock_primary_section_name = course_model_mock.primary_section_name.return_value
        create_new_course.return_value.json.return_value = {'id': mock_canvas_course_id}
        canvas_course_site_wizard.controller.create_canvas_course(self.sis_course_id)
        create_course_section.assert_called_with(request_ctx=SDK_CONTEXT, course_id=mock_canvas_course_id,
                                                 course_section_name=mock_primary_section_name,
                                                 course_section_sis_section_id=self.sis_course_id)

    def test_when_create_course_section_method_raises_exception(self, get_course_data,
                                                                create_course_section, create_new_course):
        """
        Test to assert that a RenderableException is raised when the create_course_section method
        throws an exception
        """
        create_course_section.side_effect = Exception
        with self.assertRaises(RenderableException):
            canvas_course_site_wizard.controller.create_canvas_course(self.sis_course_id)

    def test_when_create_course_section_method_raises_httperror(self, get_course_data,
                                                                create_course_section, create_new_course):
        """
        Test to assert that a RenderableException is raised when the create_course_section SDK call
        throws an HTTPError
        """
        create_course_section.side_effect = HTTPError
        with self.assertRaises(RenderableException):
            canvas_course_site_wizard.controller.create_canvas_course(self.sis_course_id)
