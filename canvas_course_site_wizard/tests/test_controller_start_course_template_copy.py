from canvas_course_site_wizard.controller import start_course_template_copy
from canvas_course_site_wizard.models import SISCourseData
from canvas_course_site_wizard.exceptions import NoTemplateExistsForSchool
from unittest import TestCase
from mock import patch, DEFAULT, Mock
from django.core.exceptions import ObjectDoesNotExist

import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)

 
@patch.multiple('canvas_course_site_wizard.controller', get_template_for_school=DEFAULT, content_migrations=DEFAULT, CanvasContentMigrationJob=DEFAULT, SDK_CONTEXT=DEFAULT)
class StartCourseTemplateCopyTest(TestCase):
    longMessage = True

    def setUp(self):
        self.template_id = 54321
        self.canvas_course_id = 9999
        self.user_id = 123
        self.sis_course_data = Mock(
            pk=88323,
            spec=SISCourseData,
            school_code='fas',
        )
        self.content_migration_json = {
            'id': '52322',
            'progress_url': 'http://canvas.instructure.com/api/v1/progress/5',
        }
    
    def assertEqualForContentMigrationJobCreation(self, param_key, expected_result, content_migration_sdk_call_mock, content_migration_job_db_mock):
        """
        Make a successful call to initiate template copy that results in a content migration row being created.   Then, verify
        that the row was created with the given key (param_key) value matching the given expected_result.
        """
        content_migration_sdk_call_mock.create_content_migration_courses.return_value.json.return_value = self.content_migration_json
        start_course_template_copy(self.sis_course_data, self.canvas_course_id, self.user_id)
        args, kwargs = content_migration_job_db_mock.objects.create.call_args
        self.assertEqual(kwargs.get(param_key), expected_result)

    def test_get_template_for_school_called_with_school_code(self, get_template_for_school, **kwargs):
        """
        Test that controller method calls get_template_for_school with expected parameter
        """
        start_course_template_copy(self.sis_course_data, self.canvas_course_id, self.user_id)
        get_template_for_school.assert_called_with(self.sis_course_data.school_code)

    def test_custom_exception_raised_if_no_template_for_school(self, get_template_for_school, **kwargs):
        """
        Test that if an ObjectDoesNotExist exception gets triggered when retrieving the school
        template, a NoTemplateExistsForCourse exception is raised back to the caller
        """
        get_template_for_school.side_effect = ObjectDoesNotExist
        with self.assertRaises(NoTemplateExistsForSchool):
            start_course_template_copy(self.sis_course_data, self.canvas_course_id, self.user_id)

    def test_content_migration_copy_called_with_context_positional_arg(self, content_migrations, SDK_CONTEXT, **kwargs):
        """
        Test that SDK call to initiate course copy has SDK_CONTEXT as a positional argument
        """
        start_course_template_copy(self.sis_course_data, self.canvas_course_id, self.user_id)
        args, kwargs = content_migrations.create_content_migration_courses.call_args
        self.assertTrue(SDK_CONTEXT in args)

    def test_content_migration_copy_called_with_canvas_course_id_positional_arg(self, content_migrations, **kwargs):
        """
        Test that SDK call to initiate course copy has the canvas_course_id as a positional argument
        """
        start_course_template_copy(self.sis_course_data, self.canvas_course_id, self.user_id)
        args, kwargs = content_migrations.create_content_migration_courses.call_args
        self.assertTrue(self.canvas_course_id in args)

    def test_content_migration_copy_called_with_expected_migration_type_keyword(self, content_migrations, **kwargs):
        """
        Test that SDK call to initiate course copy has the right migration_type specified
        """
        expected_migration_type = 'course_copy_importer'
        start_course_template_copy(self.sis_course_data, self.canvas_course_id, self.user_id)
        args, kwargs = content_migrations.create_content_migration_courses.call_args
        self.assertEqual(kwargs.get('migration_type'), expected_migration_type)

    def test_content_migration_copy_called_with_expected_templated_id_keyword(self, content_migrations, get_template_for_school, **kwargs):
        """
        Test that SDK call to initiate course copy has the expected template id specified
        """
        get_template_for_school.return_value = self.template_id
        start_course_template_copy(self.sis_course_data, self.canvas_course_id, self.user_id)
        args, kwargs = content_migrations.create_content_migration_courses.call_args
        self.assertEqual(kwargs.get('settings_source_course_id'), self.template_id)

    def test_content_migration_job_row_created_with_canvas_course_id(self, content_migrations, CanvasContentMigrationJob, **kwargs):
        """
        Test that a content migration job row was created with the expected canvas course id
        """
        self.assertEqualForContentMigrationJobCreation(
            'canvas_course_id',
            self.canvas_course_id,
            content_migrations,
            CanvasContentMigrationJob,
        )

    def test_content_migration_job_row_created_with_sis_course_id(self, content_migrations, CanvasContentMigrationJob, **kwargs):
        """
        Test that a content migration job row was created with the expected sis course id
        """
        self.assertEqualForContentMigrationJobCreation(
            'sis_course_id',
            self.sis_course_data.pk,
            content_migrations,
            CanvasContentMigrationJob,
        )

    def test_content_migration_job_row_created_with_content_migration_id(self, content_migrations, CanvasContentMigrationJob, **kwargs):
        """
        Test that a content migration job row was created with the expected id value of the SDK response
        """
        self.assertEqualForContentMigrationJobCreation(
            'content_migration_id',
            self.content_migration_json['id'],
            content_migrations,
            CanvasContentMigrationJob,
        )

    def test_content_migration_job_row_created_with_status_url(self, content_migrations, CanvasContentMigrationJob, **kwargs):
        """
        Test that a content migration job row was created with the expected progress url from the SDK response
        """
        self.assertEqualForContentMigrationJobCreation(
            'status_url',
            self.content_migration_json['progress_url'],
            content_migrations,
            CanvasContentMigrationJob,
        )

    def test_content_migration_job_row_created_with_current_user_id(self, content_migrations, CanvasContentMigrationJob, **kwargs):
        """
        Test that a content migration job row was created with the user_id passed into the method
        """
        self.assertEqualForContentMigrationJobCreation(
            'created_by_user_id',
            self.user_id,
            content_migrations,
            CanvasContentMigrationJob,
        )
