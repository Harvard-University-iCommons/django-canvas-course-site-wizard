
from django.test import TestCase
from mock import patch, ANY, DEFAULT, Mock, MagicMock
from django.db.models import Q

from canvas_course_site_wizard.models import CanvasContentMigrationJob
from canvas_course_site_wizard.management.commands import process_async_jobs
from django.test.utils import override_settings
import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)

class CommandsTestCase(TestCase):
    """
    tests for the process_async_jobs management command.
    """
    def setUp(self):
        self.canvas_course_id = 12345
        self.sis_course_id = 6789
        self.content_migration_id = 123
        self.status_url = 'http://example.com/1234'
        self.created_by_user_id= '123'
        self.workflow_state = 'queued'
        self.status_check = {
            'workflow_state': 'completed',
        }
        
    @patch('canvas_course_site_wizard.management.commands.process_async_jobs.CanvasContentMigrationJob.objects.filter')
    def test_process_async_jobs_cm_filter_called_with(self, filter_mock):
        """ 
        test process_async_jobs called CanvasContentMigrationJob.objects.filter with one argument
        """
        cmd = process_async_jobs.Command()
        opts = {} 
        cmd.handle_noargs(**opts)
        filter_mock.assert_called_once_with(ANY)


    @patch('canvas_course_site_wizard.management.commands.process_async_jobs.client.get')
    def test_process_async_jobs_cm_assert_that_client_get_is_called_once_with_the_correct_url(self, client_mock):
        """ 
        ** Integration test **
        assert that client.get is called with the job.status_url. Note that this 
        will most likely change as the method of getting the job_id can be streamlined. At the moment
        we store the progress url in the jobs table, but we only really need to store the job_id. If that 
        change happens this test will need to be replaced. 
        """
        canvas_course_id = 12345
        sis_course_id = 6789
        content_migration_id = 123
        status_url = 'http://example.com/1234'
        workflow_state = 'queued' 

        CanvasContentMigrationJob.objects.create(
            canvas_course_id=canvas_course_id, 
            sis_course_id=sis_course_id, 
            content_migration_id=content_migration_id, 
            status_url=status_url,
            workflow_state=workflow_state)

        cmd = process_async_jobs.Command()
        opts = {} 
        cmd.handle_noargs(**opts)
        client_mock.assert_called_with(ANY, 'http://example.com/1234')

    @override_settings(CANVAS_EMAIL_NOTIFICATION= {'course_migration_success_subject':'xyz', 'course_migration_success_body':'abc'})
    @patch('canvas_course_site_wizard.management.commands.process_async_jobs.finalize_new_canvas_course')
    @patch('canvas_course_site_wizard.management.commands.process_async_jobs.send_email_helper')
    @patch('canvas_course_site_wizard.management.commands.process_async_jobs.get_canvas_user_profile')
    @patch('canvas_course_site_wizard.management.commands.process_async_jobs.client.get')
    def test_process_async_jobs_invokes_correct_methods_on_completed_status(self,
     client_mock, get_canvas_user_profile, email_helper_mock, finalize_mock):
        """
        test that the send_email_helper and get_canvas_user_profile helper method are called
        with the right params when the workflow_state of the job changes to 'completed'
        """

        CanvasContentMigrationJob.objects.create(
            canvas_course_id = self.canvas_course_id, 
            sis_course_id = self.sis_course_id, 
            content_migration_id = self.content_migration_id, 
            status_url = self.status_url,
            created_by_user_id = self.created_by_user_id,
            workflow_state = self.workflow_state)
       
        client_mock.return_value.json.return_value = {
            'workflow_state': 'completed',
        }
        get_canvas_user_profile.return_value = {
            'primary_email': 'a@a.com',
        }
        email_helper_mock.return_value= DEFAULT
        cmd = process_async_jobs.Command()
        opts = {} 
        cmd.handle_noargs(**opts)
        get_canvas_user_profile.assert_called_with(self.created_by_user_id)
        email_helper_mock.assert_called_with(ANY, ANY, ANY)


    @override_settings(CANVAS_EMAIL_NOTIFICATION= {'course_migration_success_subject':'xyz', 'course_migration_success_body':'abc'})
    @patch('canvas_course_site_wizard.management.commands.process_async_jobs.finalize_new_canvas_course')
    @patch('canvas_course_site_wizard.management.commands.process_async_jobs.send_failure_email')
    @patch('canvas_course_site_wizard.management.commands.process_async_jobs.get_canvas_user_profile')
    @patch('canvas_course_site_wizard.management.commands.process_async_jobs.client.get')
    def test_process_async_jobs_invokes_correct_methods_on_failed_status(self,
     client_mock, get_canvas_user_profile, email_failure_mock, finalize_mock):
        """
        test that the send_failure_email and get_canvas_user_profile helper method are called
        with the right params when the workflow_state of the job changes to 'failed'
        """

        CanvasContentMigrationJob.objects.create(
            canvas_course_id = self.canvas_course_id, 
            sis_course_id = self.sis_course_id, 
            content_migration_id = self.content_migration_id, 
            status_url = self.status_url,
            created_by_user_id = self.created_by_user_id,
            workflow_state = self.workflow_state)
       
        client_mock.return_value.json.return_value = {
            'workflow_state': 'failed',
        }
        get_canvas_user_profile.return_value = {
            'primary_email': 'a@a.com',
        }

                            # send_failure_email(user_profile['primary_email'], job.sis_course_id)

        email_failure_mock.return_value= DEFAULT
        cmd = process_async_jobs.Command()
        opts = {} 
        cmd.handle_noargs(**opts)
        get_canvas_user_profile.assert_called_with(self.created_by_user_id)
        email_failure_mock.assert_called_with(ANY, ANY)

    @override_settings(CANVAS_EMAIL_NOTIFICATION= {'course_migration_success_subject':'xyz', 'course_migration_success_body':'abc'})
    @patch('canvas_course_site_wizard.management.commands.process_async_jobs.finalize_new_canvas_course')
    @patch('canvas_course_site_wizard.management.commands.process_async_jobs.send_failure_email')
    @patch('canvas_course_site_wizard.management.commands.process_async_jobs.get_canvas_user_profile')
    @patch('canvas_course_site_wizard.management.commands.process_async_jobs.client.get')
    def test_process_async_jobs_sends_failure_email_when_error_in_finalize_method(self,
     client_mock, get_canvas_user_profile, email_failure_mock, finalize_mock):
        """
        test that the sync jobs send a failure email notification  on any exception raised by finalize_new_canvas_course
        """

        CanvasContentMigrationJob.objects.create(
            canvas_course_id = self.canvas_course_id, 
            sis_course_id = self.sis_course_id, 
            content_migration_id = self.content_migration_id, 
            status_url = self.status_url,
            created_by_user_id = self.created_by_user_id,
            workflow_state = self.workflow_state)
        client_mock.return_value.json.return_value = {
            'workflow_state': 'completed',
        }
        get_canvas_user_profile.return_value = {
            'primary_email': 'a@a.com',
        }

        finalize_mock.side_effect = Exception
        email_failure_mock.return_value= DEFAULT
        cmd = process_async_jobs.Command()
        opts = {} 
        cmd.handle_noargs(**opts)
        email_failure_mock.assert_called_with(ANY, ANY)

    @override_settings(CANVAS_EMAIL_NOTIFICATION= {'course_migration_success_subject':'xyz', 'course_migration_success_body':'abc'})
    @patch('canvas_course_site_wizard.management.commands.process_async_jobs.finalize_new_canvas_course')
    @patch('canvas_course_site_wizard.management.commands.process_async_jobs.send_failure_email')
    @patch('canvas_course_site_wizard.management.commands.process_async_jobs.get_canvas_user_profile')
    @patch('canvas_course_site_wizard.management.commands.process_async_jobs.client.get')
    def test_process_async_jobs_sends_failure_email_when_any_exception_occurs(self,
     client_mock, get_canvas_user_profile, email_failure_mock, finalize_mock):
        """
        test that the sync jobs send a failure email notification  on any exception raised by finalize_new_canvas_course
        """

        CanvasContentMigrationJob.objects.create(
            canvas_course_id = self.canvas_course_id, 
            sis_course_id = self.sis_course_id, 
            content_migration_id = self.content_migration_id, 
            status_url = self.status_url,
            created_by_user_id = self.created_by_user_id,
            workflow_state = self.workflow_state)

        client_mock.side_effect = Exception
        get_canvas_user_profile.return_value = {
            'primary_email': 'a@a.com',
        }

        # finalize_mock.side_effect = Exception
        email_failure_mock.return_value= DEFAULT
        cmd = process_async_jobs.Command()
        opts = {} 
        cmd.handle_noargs(**opts)
        email_failure_mock.assert_called_with(ANY, ANY)

    @override_settings(CANVAS_EMAIL_NOTIFICATION= {'course_migration_success_subject':'xyz', 'course_migration_success_body':'abc'})
    @patch('canvas_course_site_wizard.management.commands.process_async_jobs.finalize_new_canvas_course')
    @patch('canvas_course_site_wizard.management.commands.process_async_jobs.send_email_helper')
    @patch('canvas_course_site_wizard.management.commands.process_async_jobs.get_canvas_user_profile')
    @patch('canvas_course_site_wizard.management.commands.process_async_jobs.client.get')
    # @patch('canvas_course_site_wizard.management.commands.process_async_jobs.jobs.job.save')
    def test_process_async_jobs_raisess_exception_thrown_by_get_user_profile(self, 
     client_mock, get_canvas_user_profile, email_helper_mock, finalize_mock):
        """
        Test that an exception  is raised when  get_canvas_user_profile method throws an exception
        """
        job = CanvasContentMigrationJob.objects.create(
            canvas_course_id = self.canvas_course_id, 
            sis_course_id = self.sis_course_id, 
            content_migration_id = self.content_migration_id, 
            status_url = self.status_url,
            created_by_user_id = self.created_by_user_id,
            workflow_state = self.workflow_state)
       
        client_mock.return_value.json.return_value = {
            'workflow_state': 'completed',
        }
        get_canvas_user_profile.side_effect = Exception
        save_mock = MagicMock(update_fields=['workflow_state'])
        job.save =  save_mock 

        cmd = process_async_jobs.Command()
        opts = {} 
        cmd.handle_noargs(**opts)
        self.assertRaises( Exception, process_async_jobs.Command())


    @override_settings(CANVAS_EMAIL_NOTIFICATION= {'course_migration_success_subject':'xyz', 'course_migration_success_body':'abc'})
    @patch('canvas_course_site_wizard.management.commands.process_async_jobs.finalize_new_canvas_course')
    @patch('canvas_course_site_wizard.management.commands.process_async_jobs.send_email_helper')
    @patch('canvas_course_site_wizard.management.commands.process_async_jobs.get_canvas_user_profile')
    @patch('canvas_course_site_wizard.management.commands.process_async_jobs.client.get')
    def test_process_async_jobs_raises_exception_thrown_by_send_email_helper(self,
     client_mock, get_canvas_user_profile, email_helper_mock, finalize_mock ):
        """
        Test that an exception  is raised when  send_email_helper method throws an exception
        """
        CanvasContentMigrationJob.objects.create(
            canvas_course_id = self.canvas_course_id, 
            sis_course_id = self.sis_course_id, 
            content_migration_id = self.content_migration_id, 
            status_url = self.status_url,
            created_by_user_id = self.created_by_user_id,
            workflow_state = self.workflow_state)
       
        client_mock.return_value.json.return_value = {
            'workflow_state': 'completed',
        }
        get_canvas_user_profile.return_value = {
            'primary_email': 'a@a.com',
        }       
        email_helper_mock.side_effect = Exception

        cmd = process_async_jobs.Command()
        opts = {} 
        cmd.handle_noargs(**opts)
        self.assertRaises( Exception, process_async_jobs.Command())


    @override_settings(CANVAS_EMAIL_NOTIFICATION= {'course_migration_success_subject':'xyz', 'course_migration_success_body':'abc'})
    @patch('canvas_course_site_wizard.management.commands.process_async_jobs.finalize_new_canvas_course')
    @patch('canvas_course_site_wizard.management.commands.process_async_jobs.logger.error')
    @patch('canvas_course_site_wizard.management.commands.process_async_jobs.send_failure_email')
    @patch('canvas_course_site_wizard.management.commands.process_async_jobs.send_email_helper')
    @patch('canvas_course_site_wizard.management.commands.process_async_jobs.get_canvas_user_profile')
    @patch('canvas_course_site_wizard.management.commands.process_async_jobs.client.get')
    def test_process_async_jobs_logs_exception(self,
     client_mock, get_canvas_user_profile, email_helper_mock, email_failure_mock, log_error, finalize_mock):
        """
        Test that an exception  is properly logged by the async job
        """
        CanvasContentMigrationJob.objects.create(
            canvas_course_id = self.canvas_course_id, 
            sis_course_id = self.sis_course_id, 
            content_migration_id = self.content_migration_id, 
            status_url = self.status_url,
            created_by_user_id = self.created_by_user_id,
            workflow_state = self.workflow_state)

        # saved_obj = CanvasContentMigrationJob.objects.save( workflow_state = 'completed')
        client_mock.return_value.json.return_value = {
            'workflow_state': 'completed',
        }
        get_canvas_user_profile.side_effect = Exception

        cmd = process_async_jobs.Command()
        opts = {} 
        cmd.handle_noargs(**opts)
        self.assertTrue(log_error.called)

