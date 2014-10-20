
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
        assert that the job_id is properly parsed from the returned job status_url. Note that this 
        will most likely change as the method of getting the job_id can be streamlined. At the moment
        we store the progress url in the jobs table, but we only really need to store the job_id. Once that 
        is in place this test will need to be replaced. 
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




