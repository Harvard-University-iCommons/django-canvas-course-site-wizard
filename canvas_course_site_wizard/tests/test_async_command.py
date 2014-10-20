
from django.test import TestCase
from mock import patch, ANY
from django.db.models import Q
from canvas_course_site_wizard.models import CanvasContentMigrationJob
from django.core.management import call_command
from canvas_course_site_wizard.management.commands import process_async_jobs
import json


class CommandsTestCase(TestCase):
    """
    tests for the process_async_jobs management command.
    """

    def test_process_async_jobs_check_workflow_type_returns_true_when_type_is_in_list(self):
        """
        Test that check_workflow_type returns True when the workflow type passed in 
        is one of the expected values
        """
        cmd = process_async_jobs.Command()
        result = cmd.check_workflow_type('queued')
        self.assertEqual(result, True)


    def test_process_async_jobs_check_workflow_type_returns_false_when_type_is_not_in_list(self):
        """
        Test that check_workflow_type returns False when the workflow type passed in 
        is NOT one of the expected values
        """
        cmd = process_async_jobs.Command()
        result = cmd.check_workflow_type('other')
        self.assertEqual(result, False)


    @patch('canvas_course_site_wizard.management.commands.process_async_jobs.CanvasContentMigrationJob.objects.filter')
    def test_process_async_jobs_cm_filter_called_with(self, filter_mock):
        """ 
        test process_async_jobs called CanvasContentMigrationJob.objects.filter with one argument
        """
        cmd = process_async_jobs.Command()
        opts = {} 
        cmd.handle_noargs(**opts)
        filter_mock.assert_called_once_with(ANY)

    @patch('canvas_course_site_wizard.management.commands.process_async_jobs.query_progress')
    def test_process_async_jobs_cm_raises_exception_when_workflow_type_is_not_expected(self, query_mock):
        """ 
        ** Integration test **
        assert that the job_id is properly parsed from the returned job status_url
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
        query_mock.assert_called_once_with(ANY, '1234')




