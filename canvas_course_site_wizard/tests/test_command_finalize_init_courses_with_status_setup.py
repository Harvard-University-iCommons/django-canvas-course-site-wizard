from django.test import TestCase
from mock import patch, ANY, DEFAULT, Mock, MagicMock, call
from canvas_course_site_wizard.management.commands.finalize_bulk_create_jobs import _init_courses_with_status_setup
from canvas_course_site_wizard.models import CanvasContentMigrationJobProxy
from canvas_course_site_wizard.management.commands import finalize_bulk_create_jobs
from canvas_course_site_wizard.exceptions import (NoTemplateExistsForSchool,
                                                  CanvasCourseAlreadyExistsError,
                                                  ContentMigrationJobCreationError)
def start_job_with_noargs():
    cmd = finalize_bulk_create_jobs.Command()
    cmd.handle_noargs()

class ContentMigrationJob:

    def __init__(self, pk, bulk_job_id, created_by_user_id, sis_course_id, state):
        self.pk = pk
        self.bulk_job_id = bulk_job_id
        self.created_by_user_id = created_by_user_id
        self.sis_course_id = sis_course_id
        self.workflow_state = state

    def update_workflow_state(self, state):
        self.workflow_state = state


@patch.multiple('canvas_course_site_wizard.management.commands.finalize_bulk_create_jobs',
                get_course_data=DEFAULT, create_canvas_course=DEFAULT, start_course_template_copy=DEFAULT)
class FinalizeInitCoursesWithStatusSetupCommandTests(TestCase):

    def setUp(self):
        self.user_id = '12345678'
        self.bulk_job_id = 12345
        self.school_code = 'colgsas'
        self.sis_term_id = 4579
        self.courses = [123, 456, 789, 1011, 1012, 1013, 1014, 1015]
        self.course_data_calls = []
        self.create_course_calls = []
        self.finalize_calls = []
        self.template_copy_calls = []
        self.cm_jobs = []
        self.create_logger_calls = []
        self.template_calls = []
        self.content_migration_error_calls = []
        for idx, course in enumerate(self.courses):
            self.create_course_calls.append(call(course, self.user_id, bulk_job_id=self.bulk_job_id))
            self.create_course_calls.append(ANY)
            self.course_data_calls.append(call(course))
            self.finalize_calls.append(call(ANY, course, 'sis_user_id:%s' % self.user_id, bulk_job_id=self.bulk_job_id))
            self.template_copy_calls.append(call(ANY, ANY, self.user_id, bulk_job_id=self.bulk_job_id))
            migration_job = ContentMigrationJob(
                idx,
                self.bulk_job_id,
                self.user_id,
                course,
                CanvasContentMigrationJobProxy.STATUS_SETUP
            )
            self.cm_jobs.append(migration_job)
            self.create_logger_calls.append(call('course already exists in canvas with id %s' % course))
            self.content_migration_error_calls.append(call('content migration error for course with id %s' % course))
            self.template_calls.append(call('no template for course instance id %s' % course))

    @patch('canvas_course_site_wizard.management.commands.finalize_bulk_create_jobs.CanvasContentMigrationJobProxy.get_jobs_by_workflow_state')
    def test_1237(self, mock_getjobs, get_course_data, create_canvas_course, start_course_template_copy):
        """
        test that create_canvas_course is called with all the courses that have a status of 'setup'
        """
        mock_getjobs.return_value = self.cm_jobs
        _init_courses_with_status_setup()
        create_canvas_course.assert_has_calls(self.create_course_calls)

    @patch('canvas_course_site_wizard.management.commands.finalize_bulk_create_jobs.logger.exception')
    @patch('canvas_course_site_wizard.management.commands.finalize_bulk_create_jobs.CanvasContentMigrationJobProxy.get_jobs_by_workflow_state')
    def test_1238(self, mock_getjobs, mock_logger, get_course_data, create_canvas_course, start_course_template_copy):
        """
        test that create_canvas_course is called with all the courses that have a status of 'setup'
        """
        mock_getjobs.return_value = self.cm_jobs
        create_canvas_course.side_effect = CanvasCourseAlreadyExistsError(msg_details=123)
        _init_courses_with_status_setup()
        mock_logger.assert_has_calls(self.create_logger_calls)

    @patch('canvas_course_site_wizard.management.commands.finalize_bulk_create_jobs.logger.exception')
    @patch('canvas_course_site_wizard.management.commands.finalize_bulk_create_jobs.CanvasContentMigrationJobProxy.get_jobs_by_workflow_state')
    def test_1238(self, mock_getjobs, mock_logger, get_course_data, create_canvas_course, start_course_template_copy):
        """
        test that create_canvas_course is called with all the courses that have a status of 'setup'
        """
        mock_getjobs.return_value = self.cm_jobs
        create_canvas_course.side_effect = ContentMigrationJobCreationError(msg_details=123)
        _init_courses_with_status_setup()
        mock_logger.assert_has_calls(self.content_migration_error_calls)

    @patch('canvas_course_site_wizard.management.commands.finalize_bulk_create_jobs.logger.exception')
    @patch('canvas_course_site_wizard.management.commands.finalize_bulk_create_jobs.CanvasContentMigrationJobProxy.get_jobs_by_workflow_state')
    def test_1238(self, mock_getjobs, mock_logger, get_course_data, create_canvas_course, start_course_template_copy):
        """
        test that create_canvas_course is called with all the courses that have a status of 'setup'
        """
        mock_getjobs.return_value = self.cm_jobs
        start_course_template_copy.side_effect = NoTemplateExistsForSchool(self.school_code)
        _init_courses_with_status_setup()
        mock_logger.assert_has_calls(self.template_calls)