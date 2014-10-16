from canvas_course_site_wizard.controller import start_course_template_copy
from canvas_course_site_wizard.models import SISCourseData
from canvas_course_site_wizard.exceptions import NoTemplateExistsForSchool
from unittest import TestCase
from mock import patch, DEFAULT, Mock
from django.core.exceptions import ObjectDoesNotExist

import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)

 
@patch.multiple('canvas_course_site_wizard.controller', get_template_for_school=DEFAULT)
class StartCourseTemplateCopyTest(TestCase):
    longMessage = True

    def setUp(self):
        self.template_id = 54321
        self.canvas_course_id = 9999
        self.sis_course_data = Mock(
            spec=SISCourseData,
            school_code='fas',
        )
    
    def test_get_template_for_school_called_with_school_code(self, get_template_for_school):
        """
        Test that controller method calls get_template_for_school with expected parameter
        """
        start_course_template_copy(self.sis_course_data, self.canvas_course_id)
        get_template_for_school.assert_called_with(self.sis_course_data.school_code)

    def test_custom_exception_raised_if_no_template_for_school(self, get_template_for_school):
        """
        Test that if an ObjectDoesNotExist exception gets triggered when retrieving the school
        template, a NoTemplateExistsForCourse exception is raised back to the caller
        """
        get_template_for_school.side_effect = ObjectDoesNotExist
        with self.assertRaises(NoTemplateExistsForSchool):
            start_course_template_copy(self.sis_course_data, self.canvas_course_id)

