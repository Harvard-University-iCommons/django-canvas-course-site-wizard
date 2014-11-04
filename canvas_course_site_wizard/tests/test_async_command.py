
from django.test import TestCase
from mock import patch, ANY, DEFAULT, Mock, MagicMock
from canvas_course_site_wizard.models import CanvasContentMigrationJob
from canvas_course_site_wizard.management.commands import process_async_jobs
from django.test.utils import override_settings


@override_settings(CANVAS_EMAIL_NOTIFICATION={'course_migration_success_subject': 'xyz', 'course_migration_success_body': 'abc'})
@patch.multiple(
    'canvas_course_site_wizard.management.commands.process_async_jobs',
    send_failure_email=DEFAULT,
    logger=DEFAULT,
    finalize_new_canvas_course=DEFAULT,
    send_email_helper=DEFAULT,
    get_canvas_user_profile=DEFAULT,
    client=DEFAULT
)
class CommandsTestCase(TestCase):
    """
    tests for the process_async_jobs management command.
    """
    def setUp(self):
        self.canvas_course_id = 12345
        self.sis_course_id = 6789
        self.content_migration_id = 123
        self.status_url = 'http://example.com/1234'
        self.created_by_user_id = '123'
        self.workflow_state = 'queued'
        self.status_check = {
            'workflow_state': 'completed',
        }

    def create_migration_job_from_setup(self):
        """ Create and return a new CanvasContentMigrationJob using values in setUp and return """
        return CanvasContentMigrationJob.objects.create(
            canvas_course_id=self.canvas_course_id,
            sis_course_id=self.sis_course_id,
            content_migration_id=self.content_migration_id,
            status_url=self.status_url,
            created_by_user_id=self.created_by_user_id,
            workflow_state=self.workflow_state
        )

    @patch('canvas_course_site_wizard.management.commands.process_async_jobs.CanvasContentMigrationJob.objects.filter')
    def test_process_async_jobs_cm_filter_called_with(self, filter_mock, **kwargs):
        """
        test process_async_jobs called CanvasContentMigrationJob.objects.filter with one argument
        """
        cmd = process_async_jobs.Command()
        cmd.handle_noargs()
        filter_mock.assert_called_once_with(ANY)

    def test_process_async_jobs_cm_assert_that_client_get_is_called_once_with_the_correct_url(self, client, **kwargs):
        """
        ** Integration test **
        assert that client.get is called with the job.status_url. Note that this
        will most likely change as the method of getting the job_id can be streamlined. At the moment
        we store the progress url in the jobs table, but we only really need to store the job_id. If that
        change happens this test will need to be replaced.
        """

        self.create_migration_job_from_setup()
        cmd = process_async_jobs.Command()
        cmd.handle_noargs()
        client.get.assert_called_with(ANY, self.status_url)

    def test_process_async_jobs_invokes_correct_methods_on_completed_status(self, client, get_canvas_user_profile, send_email_helper, **kwargs):
        """
        test that the send_email_helper and get_canvas_user_profile helper method are called
        with the right params when the workflow_state of the job changes to 'completed'
        """

        self.create_migration_job_from_setup()
        client.get.return_value.json.return_value = {
            'workflow_state': 'completed',
        }
        get_canvas_user_profile.return_value = {
            'primary_email': 'a@a.com',
        }
        cmd = process_async_jobs.Command()
        cmd.handle_noargs()
        get_canvas_user_profile.assert_called_with(self.created_by_user_id)
        send_email_helper.assert_called_once_with(ANY, ANY, ANY)

    def test_process_async_jobs_invokes_correct_methods_on_failed_status(self, client, get_canvas_user_profile, send_email_helper, **kwargs):
        """
        test that the send_failure_email and get_canvas_user_profile helper method is called
        when the workflow_state of the job changes to 'failed'
        """

        self.create_migration_job_from_setup()
       
        client.get.return_value.json.return_value = {
            'workflow_state': 'failed',
        }
        get_canvas_user_profile.return_value = {
            'primary_email': 'a@a.com',
        }

        cmd = process_async_jobs.Command()
        cmd.handle_noargs()
        get_canvas_user_profile.assert_called_with(self.created_by_user_id)
        send_email_helper.assert_called_with_any(ANY, ANY)

    def test_process_async_jobs_sends_failure_email_when_error_in_finalize_method(self, client, get_canvas_user_profile, finalize_new_canvas_course, send_failure_email, **kwargs):
        """
        test that the sync jobs send a failure email notification on any exception raised by finalize_new_canvas_course
        """

        self.create_migration_job_from_setup()
        client.get.return_value.json.return_value = {
            'workflow_state': 'completed',
        }
        get_canvas_user_profile.return_value = {
            'primary_email': 'a@a.com',
        }

        finalize_new_canvas_course.side_effect = Exception
        cmd = process_async_jobs.Command()
        cmd.handle_noargs()
        send_failure_email.assert_called_with(ANY, ANY)

    def test_process_async_jobs_sends_failure_email_when_any_exception_occurs(self, client, get_canvas_user_profile, send_email_helper, finalize_new_canvas_course, logger, send_failure_email, **kwargs):
        """
        test that the sync jobs send a failure email notification on an exception during job processing
        """

        self.create_migration_job_from_setup()
        client.get.side_effect = Exception
        get_canvas_user_profile.return_value = {
            'primary_email': 'a@a.com',
        }

        cmd = process_async_jobs.Command()
        cmd.handle_noargs()
        send_failure_email.assert_called_with(ANY, ANY)

    def test_process_async_jobs_logs_exception_thrown_by_send_email_helper(self, client, get_canvas_user_profile, send_email_helper, finalize_new_canvas_course, logger, **kwargs):
        """
        Test that an exception is raised when send_email_helper method throws an exception
        """

        self.create_migration_job_from_setup()
       
        client.get.return_value.json.return_value = {
            'workflow_state': 'completed',
        }
        get_canvas_user_profile.return_value = {
            'primary_email': 'a@a.com',
        }
        send_email_helper.side_effect = Exception

        cmd = process_async_jobs.Command()
        cmd.handle_noargs()
        self.assertTrue(logger.exception.called)

    def test_process_async_jobs_logs_exception(self, client, get_canvas_user_profile, logger, **kwargs):
        """
        Test that an exception  is properly logged by the async job
        """
        self.create_migration_job_from_setup()

        client.get.return_value.json.return_value = {
            'workflow_state': 'completed',
        }
        get_canvas_user_profile.side_effect = Exception

        cmd = process_async_jobs.Command()
        cmd.handle_noargs()
        self.assertTrue(logger.exception.called)

    def test_job_workflow_state_saved_when_status_complete_and_finalize_throws_exception(self, client, get_canvas_user_profile, send_email_helper, finalize_new_canvas_course, **kwargs):
        """ Test that the content migration workflow state is updated regardless of whether finalizing throws an exception """
        migration = self.create_migration_job_from_setup()
        client.get.return_value.json.return_value = {
            'workflow_state': 'completed',
        }
        finalize_new_canvas_course.side_effect = Exception

        cmd = process_async_jobs.Command()
        cmd.handle_noargs()
        cm = CanvasContentMigrationJob.objects.get(pk=migration.pk)
        self.assertEqual(cm.workflow_state, CanvasContentMigrationJob.STATUS_COMPLETED)

    def test_job_workflow_state_saved_when_status_failed_and_finalize_throws_exception(self, client, get_canvas_user_profile, send_email_helper, finalize_new_canvas_course, **kwargs):
        """ Test that the content migration workflow state is updated regardless of whether finalizing throws an exception """
        migration = self.create_migration_job_from_setup()
        client.get.return_value.json.return_value = {
            'workflow_state': 'failed',
        }
        finalize_new_canvas_course.side_effect = Exception

        cmd = process_async_jobs.Command()
        cmd.handle_noargs()
        cm = CanvasContentMigrationJob.objects.get(pk=migration.pk)
        self.assertEqual(cm.workflow_state, CanvasContentMigrationJob.STATUS_FAILED)
