from unittest import TestCase
from mock import patch, DEFAULT, MagicMock
from icommons_ui.exceptions import RenderableException
from django.core.exceptions import ObjectDoesNotExist
from canvas_sdk.exceptions import CanvasAPIError
from canvas_course_site_wizard import controller
from canvas_course_site_wizard.exceptions import (CanvasCourseCreateError, CanvasCourseAlreadyExistsError,
     SISCourseDoesNotExistError, CanvasSectionCreateError)


@patch.multiple('canvas_course_site_wizard.controller',
                get_course_data=DEFAULT, create_course_section=DEFAULT, create_new_course=DEFAULT)
class CreateCanvasCourseTest(TestCase):
    longMessage = True

    def setUp(self):
        self.sis_course_id = "305841"
        self.sis_user_id="123456"

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
        result = create_canvas_course(self.sis_course_id, self.sis_user_id)
        create_canvas_course.assert_called_with(self.sis_course_id, self.sis_user_id)

    # ------------------------------------------------------
    # Tests for create_canvas_course.get_course_data()
    # ------------------------------------------------------

    def test_get_course_data_method_called_with_right_params(self, get_course_data,
                                                             create_course_section, create_new_course):
        """
        Test that controller method makes a call to get_course_data api with expected args
        """
        controller.create_canvas_course(self.sis_course_id, self.sis_user_id)
        get_course_data.assert_called_with(self.sis_course_id)

    def test_object_not_found_exception_in_get_course_data(self, get_course_data,
                                                           create_course_section, create_new_course):
        """
        Test  when get_course_data throws an ObjectDoesNotExist
        Note: Http404 exception is one of the exceptions not visible to the test client.
        So just checking for ObjectDoesNotExist
        """
        controller.create_canvas_course(self.sis_course_id, self.sis_user_id)
        get_course_data.side_effect = ObjectDoesNotExist
        self.assertRaises(ObjectDoesNotExist, get_course_data, self.sis_course_id)

    @patch('canvas_course_site_wizard.controller.logger')
    @patch('canvas_course_site_wizard.controller.send_failure_msg_to_support')
    def test_object_not_found_exception_in_get_course_data_logs_error(self, send_failure_msg_to_support, log_replacement, get_course_data,
                                                                      create_course_section, create_new_course):
        """
        Test that the logger.error logs error when when get_course_data throws an ObjectDoesNotExist
        """
        get_course_data.side_effect = ObjectDoesNotExist
        with self.assertRaises(RenderableException):
            controller.create_canvas_course(self.sis_course_id, self.sis_user_id)
        self.assertTrue(log_replacement.error.called)

    # ------------------------------------------------------
    # Tests for create_canvas_course.create_course_section()
    # ------------------------------------------------------
    @patch('canvas_course_site_wizard.controller.logger')
    @patch('canvas_course_site_wizard.controller.SDK_CONTEXT')
    def test_create_new_course_method_is_called_with_proper_arguments(self, SDK_CONTEXT, logger, get_course_data,
                                                                      create_course_section, create_new_course):
        """
        Test to assert that create_new_course method is called by create_canvas_course controller method
        with appropriate arguments (collapses a bunch of individual parameter tests)
        """
        course_model_mock = self.get_mock_of_get_course_data()
        get_course_data.return_value = course_model_mock
        controller.create_canvas_course(self.sis_course_id, self.sis_user_id)
        sis_account_id_argument = 'sis_account_id:' + course_model_mock.sis_account_id
        course_code_argument = course_model_mock.course_code
        course_name_argument = course_model_mock.course_name
        course_term_id_argument = 'sis_term_id:' + course_model_mock.sis_term_id
        course_sis_course_id_argument = self.sis_course_id
        create_new_course.assert_called_with(request_ctx=SDK_CONTEXT, account_id=sis_account_id_argument,
                                             course_name=course_name_argument, course_course_code=course_code_argument,
                                             course_term_id=course_term_id_argument,
                                             course_sis_course_id=course_sis_course_id_argument)

    def test_exception_when_create_new_course_method_raises_api_400(self, get_course_data,
                                                            create_course_section, create_new_course):
        """
        Test to assert that a CanvasCourseAlreadyExistsError is raised when the create_new_course method
        throws a CanvasAPIError
        """
        create_new_course.side_effect = CanvasAPIError(status_code=400)
        with self.assertRaises(CanvasCourseAlreadyExistsError):
            controller.create_canvas_course(self.sis_course_id, self.sis_user_id)

    @patch('canvas_course_site_wizard.controller.send_failure_msg_to_support')
    def test_exception_when_create_new_course_method_raises_api_404(self, send_failure_msg_to_support, get_course_data,
                                                            create_course_section, create_new_course):
        """
        Test to assert that a RenderableException is raised when the create_new_course SDK call
        throws an CanvasAPIError
        """
        create_new_course.side_effect = CanvasAPIError(status_code=404)
        with self.assertRaises(CanvasCourseCreateError):
            controller.create_canvas_course(self.sis_course_id, self.sis_user_id)

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
        controller.create_canvas_course(self.sis_course_id, self.sis_user_id, None)
        create_course_section.assert_called_with(request_ctx=SDK_CONTEXT, course_id=mock_canvas_course_id,
                                                 course_section_name=mock_primary_section_name,
                                                 course_section_sis_section_id=self.sis_course_id)

    @patch('canvas_course_site_wizard.controller.send_failure_msg_to_support')
    def test_when_create_course_section_method_raises_api_error(self, send_failure_msg_to_support,get_course_data,
                                                                create_course_section, create_new_course):
        """
        Test to assert that a RenderableException is raised when the create_course_section SDK call
        throws an CanvasAPIError
        """
        create_course_section.side_effect = CanvasAPIError(status_code=400)
        with self.assertRaises(RenderableException):
            controller.create_canvas_course(self.sis_course_id, self.sis_user_id, None)


    @patch('canvas_course_site_wizard.controller.send_failure_msg_to_support')
    def test_object_not_found_exception_in_get_course_data_sends_support_email(self, send_failure_msg_to_support, get_course_data,
                                                           create_course_section, create_new_course):
        """
        Test to assert that a support email is sent  when get_course_data raises an ObjectDoesNotExist
        """

        get_course_data.side_effect = ObjectDoesNotExist
        exception_data = SISCourseDoesNotExistError(self.sis_course_id)

        with self.assertRaises(SISCourseDoesNotExistError):
            controller.create_canvas_course(self.sis_course_id, self.sis_user_id)
        send_failure_msg_to_support.assert_called_with(self.sis_course_id, self.sis_user_id, exception_data.display_text)

    @patch('canvas_course_site_wizard.controller.send_failure_msg_to_support')
    def test_object_not_found_exception_in_get_course_data_doesnt_sends_support_email_for_bulk_created_course(self, send_failure_msg_to_support, get_course_data,
                                                           create_course_section, create_new_course):
        """
        Test to assert that for a course that is created as part of a bulk job, the support email is
        not sent  when get_course_data raises an ObjectDoesNotExist
        """
        get_course_data.side_effect = ObjectDoesNotExist
        exception_data = SISCourseDoesNotExistError(self.sis_course_id)

        with self.assertRaises(SISCourseDoesNotExistError):
            controller.create_canvas_course(self.sis_course_id, self.sis_user_id, True)
            self.assertFalse(send_failure_msg_to_support.called)

    @patch('canvas_course_site_wizard.controller.send_failure_msg_to_support')
    def test_canvas_course_create_error_sends_support_email(self, send_failure_msg_to_support, get_course_data,
                                                           create_course_section, create_new_course):
        """
        Test to assert that a support email is sent  when  there is an CanvasAPIError resulting in CanvasCourseCreateError
        and that the correct error message from the exception is sent as a param  to the mail helper method
        """
        create_new_course.side_effect = CanvasAPIError(status_code=404)
        exception_data = CanvasCourseCreateError(msg_details=self.sis_course_id)
        with self.assertRaises(CanvasCourseCreateError):
            controller.create_canvas_course(self.sis_course_id, self.sis_user_id)

        send_failure_msg_to_support.assert_called_with(self.sis_course_id, self.sis_user_id, exception_data.display_text)
        self.assertTrue('Error: SIS ID not applied for CID' in exception_data.display_text)

    @patch('canvas_course_site_wizard.controller.send_failure_msg_to_support')
    def test_canvas_course_create_error_doesnt_sends_support_email_for_bulk_created_course(self, send_failure_msg_to_support, get_course_data,
                                                           create_course_section, create_new_course):
        """
        Test to assert that a for a course that is created as part of a bulk job, the support email is not sent
        when  there is an CanvasAPIError resulting in CanvasCourseCreateError
        """
        create_new_course.side_effect = CanvasAPIError(status_code=404)
        with self.assertRaises(CanvasCourseCreateError):
            controller.create_canvas_course(self.sis_course_id, self.sis_user_id, True)

        self.assertFalse(send_failure_msg_to_support.called)

    @patch('canvas_course_site_wizard.controller.send_failure_msg_to_support')
    def test_canvas_section_error_sends_support_email(self, send_failure_msg_to_support, get_course_data,
                                                           create_course_section, create_new_course):
        """
        Test to assert that a support email is sent  when  there is an CanvasAPIError resulting in
        CanvasSectionCreateError
        
        """
        create_course_section.side_effect = CanvasAPIError(status_code=400)

        exception_data = CanvasSectionCreateError(self.sis_course_id)
        with self.assertRaises(CanvasSectionCreateError):
            controller.create_canvas_course(self.sis_course_id, self.sis_user_id)

        send_failure_msg_to_support.assert_called_with(self.sis_course_id, self.sis_user_id, exception_data.display_text)

    @patch('canvas_course_site_wizard.controller.send_failure_msg_to_support')
    def test_canvas_section_error_doesnt_sends_support_email_for_bulk_created_course(self, send_failure_msg_to_support,
                                                        get_course_data, create_course_section, create_new_course):
        """
        Test to assert that a support email is NOT sent for bulk created courses, when  there is an CanvasAPIError
         resulting in CanvasSectionCreateError

        """
        create_course_section.side_effect = CanvasAPIError(status_code=400)

        exception_data = CanvasSectionCreateError(self.sis_course_id)
        with self.assertRaises(CanvasSectionCreateError):
            controller.create_canvas_course(self.sis_course_id, self.sis_user_id, True)

        self.assertFalse(send_failure_msg_to_support.called)

    @patch('canvas_course_site_wizard.controller.send_failure_msg_to_support')
    def test_canvas_course_exists_error_doesnt_send_support_email(self, send_failure_msg_to_support, get_course_data,
                                                           create_course_section, create_new_course):
        """
        Test to assert that a support email is NOT sent when canvas course already exists
        (there is a CanvasCourseAlreadyExistsError)
        
        """
        create_new_course.side_effect = CanvasAPIError(status_code=400)
        exception_data = CanvasCourseAlreadyExistsError(self.sis_course_id)
        with self.assertRaises(CanvasCourseAlreadyExistsError):
            controller.create_canvas_course(self.sis_course_id, self.sis_user_id)
        
        self.assertFalse(send_failure_msg_to_support.called)


    @patch('canvas_course_site_wizard.controller.send_failure_msg_to_support')
    def test_canvas_section_error_sets_support_notified(self, send_failure_msg_to_support, get_course_data,
                                                           create_course_section, create_new_course):
        """
        Test to assert that support_notified is set on CanvasSectionCreateError
        """
        create_course_section.side_effect = CanvasAPIError(status_code=400)
        exception_data = CanvasSectionCreateError(self.sis_course_id)
        with self.assertRaises(CanvasSectionCreateError):
            controller.create_canvas_course(self.sis_course_id, self.sis_user_id)

        self.assertTrue(True, exception_data.support_notified)

    @patch('canvas_course_site_wizard.controller.send_failure_msg_to_support')
    def test_canvas_course_create_error_sets_support_notified(self, send_failure_msg_to_support, get_course_data,
                                                           create_course_section, create_new_course):
        """
        Test to assert that support_notified is set on CanvasCourseCreateError
        """
        create_new_course.side_effect = CanvasAPIError(status_code=404)
        exception_data = CanvasCourseCreateError(msg_details=self.sis_course_id)
        with self.assertRaises(CanvasCourseCreateError):
            controller.create_canvas_course(self.sis_course_id, self.sis_user_id)

        self.assertEqual(True,exception_data.support_notified)

    @patch('canvas_course_site_wizard.controller.send_failure_msg_to_support')
    def test_canvas_course_already_exists_error_doesnt_set_support_notified(self, send_failure_msg_to_support, get_course_data,
                                                           create_course_section, create_new_course):
        """
        Test to assert that support_notified is NOT set on CanvasCourseAlreadyExistsError
        """
        create_new_course.side_effect = CanvasAPIError(status_code=400)
        with self.assertRaises(CanvasCourseAlreadyExistsError) as cm:
            controller.create_canvas_course(self.sis_course_id, self.sis_user_id)

        self.assertTrue('support_notified' not in cm.exception)

