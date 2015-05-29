from django.test import TestCase
from mock import patch, ANY, DEFAULT, Mock, MagicMock
from canvas_course_site_wizard.management.commands.finalize_bulk_create_jobs import (
    _send_notification,
    _format_notification_email_body,
    _format_notification_email_subject
)
from canvas_course_site_wizard.models import BulkCanvasCourseCreationJob as BulkJob
from canvas_course_site_wizard.management.commands import finalize_bulk_create_jobs
from django.test.utils import override_settings


def start_job_with_noargs():
    cmd = finalize_bulk_create_jobs.Command()
    cmd.handle_noargs()


def get_mock_bulk_job():
    return Mock(
        spec=BulkJob,
        id=1,
        school_id='colgsas',
        sis_term_id=1,
        created_by_user_id='12345678',
        status=BulkJob.STATUS_PENDING,
        update_status=Mock(return_value=True),
        ready_to_finalize=Mock(return_value=True)
    )


mock_settings_dict = {
    'notification_email_subject': '{} {}',
    'notification_email_body': '{} {} {}',
    'notification_email_body_failed_count': ' {}',
    'log_long_running_jobs': False
}

@override_settings(BULK_COURSE_CREATION=mock_settings_dict)
class FinalizeBulkCanvasCourseCreationJobsCommandTests(TestCase):
    """
    tests for the finalize_bulk_create_jobs management command.
    """

    @patch('canvas_course_site_wizard.management.commands.finalize_bulk_create_jobs.logger')
    @patch('canvas_course_site_wizard.management.commands.finalize_bulk_create_jobs.BulkJob.objects.get_jobs_by_status')
    def test_finalize_bulk_create_jobs_no_pending_jobs(self, m_queryset, m_logger, **kwargs):
        """ exit gracefully if there are no jobs in the table that require checking pending subjobs """
        m_queryset.return_value = BulkJob.objects.none()
        start_job_with_noargs()
        self.assertEqual(m_logger.debug.call_count, 0)
        self.assertEqual(m_logger.error.call_count, 0)
        self.assertEqual(m_logger.exception.call_count, 0)

    @patch('canvas_course_site_wizard.management.commands.finalize_bulk_create_jobs.logger')
    @patch('canvas_course_site_wizard.management.commands.finalize_bulk_create_jobs.BulkJob.objects.get_jobs_by_status')
    def test_finalize_bulk_create_jobs_pending_jobs_leave_pending(self, m_queryset, m_logger, **kwargs):
        """ exit gracefully if the pending jobs still have pending subjobs (so bulk jobs should not be finalized) """
        m_bulk_job = get_mock_bulk_job()
        m_bulk_job.ready_to_finalize.return_value = False
        m_queryset.return_value = [m_bulk_job]
        start_job_with_noargs()
        self.assertEqual(m_logger.error.call_count, 0)
        self.assertEqual(m_logger.exception.call_count, 0)

    @patch('canvas_course_site_wizard.management.commands.finalize_bulk_create_jobs._send_notification')
    @patch('canvas_course_site_wizard.management.commands.finalize_bulk_create_jobs.BulkJob.objects.get_jobs_by_status')
    def test_finalize_bulk_create_jobs_finalize_pending_jobs(self, m_queryset, m_send, **kwargs):
        """ if the pending jobs have no pending subjobs (ie they are all in terminal state) then finalize bulk jobs """
        m_bulk_job = get_mock_bulk_job()
        m_queryset.return_value = [m_bulk_job]
        start_job_with_noargs()
        # Bulk job should have been updated twice: once at the start of finalizing process, once at the end
        self.assertEqual(m_bulk_job.update_status.call_count, 2)
        m_bulk_job.update_status.assert_called_with(BulkJob.STATUS_NOTIFICATION_SUCCESSFUL)
        self.assertEqual(m_send.call_count, 1)

    @patch('canvas_course_site_wizard.management.commands.finalize_bulk_create_jobs.logger.exception')
    @patch('canvas_course_site_wizard.management.commands.finalize_bulk_create_jobs._send_notification')
    @patch('canvas_course_site_wizard.management.commands.finalize_bulk_create_jobs.BulkJob.objects.get_jobs_by_status')
    def test_finalize_bulk_create_jobs_save_fails_before_notification(self, m_queryset, m_send, m_logger, **kwargs):
        """ if we fail updating the job status before the send step, failure is logged and no notification is sent """
        m_bulk_job = get_mock_bulk_job()
        m_bulk_job.update_status.side_effect = [False]
        m_queryset.return_value = [m_bulk_job]
        start_job_with_noargs()
        self.assertEqual(m_logger.call_count, 1)
        self.assertEqual(m_bulk_job.update_status.call_count, 1)
        # Notification should not be sent for this job
        self.assertEqual(m_send.call_count, 0)

    @patch('canvas_course_site_wizard.management.commands.finalize_bulk_create_jobs.logger.exception')
    @patch('canvas_course_site_wizard.management.commands.finalize_bulk_create_jobs._send_notification')
    @patch('canvas_course_site_wizard.management.commands.finalize_bulk_create_jobs.BulkJob.objects.get_jobs_by_status')
    def test_finalize_bulk_create_jobs_save_fails_after_notification(self, m_queryset, m_send, m_logger, **kwargs):
        """ if we fail updating the job status after the notification is sent failure is still logged """
        m_bulk_job = get_mock_bulk_job()
        m_bulk_job.update_status.side_effect = [True, False]
        m_queryset.return_value = [m_bulk_job]
        start_job_with_noargs()
        self.assertEqual(m_logger.call_count, 1)
        self.assertEqual(m_bulk_job.update_status.call_count, 2)
        # Notification should already be sent for this job
        self.assertEqual(m_send.call_count, 1)


    @patch('canvas_course_site_wizard.management.commands.finalize_bulk_create_jobs.send_email_helper')
    @patch('canvas_course_site_wizard.management.commands.finalize_bulk_create_jobs._format_notification_email_body')
    @patch('canvas_course_site_wizard.management.commands.finalize_bulk_create_jobs._format_notification_email_subject')
    @patch('canvas_course_site_wizard.management.commands.finalize_bulk_create_jobs.get_canvas_user_profile')
    def test_send_notification_all_good(self, m_profile, m_subj, m_body, m_send, **kwargs):
        """ notification for finalized bulk jobs where all subjobs succeeded should reflect that fact """
        m_profile.return_value = {'primary_email': 'icommons-technical@g.harvard.edu'}
        m_bulk_job = get_mock_bulk_job()
        m_bulk_job.get_completed_subjobs_count.return_value = 1
        m_bulk_job.get_failed_subjobs_count.return_value = 0
        self.assertTrue(_send_notification(m_bulk_job))
        m_body.assert_called_once_with(ANY, ANY, 1, 0)

    @patch('canvas_course_site_wizard.management.commands.finalize_bulk_create_jobs.send_email_helper')
    @patch('canvas_course_site_wizard.management.commands.finalize_bulk_create_jobs._format_notification_email_body')
    @patch('canvas_course_site_wizard.management.commands.finalize_bulk_create_jobs._format_notification_email_subject')
    @patch('canvas_course_site_wizard.management.commands.finalize_bulk_create_jobs.get_canvas_user_profile')
    def test_send_notification_mixed_results(self, m_profile, m_subj, m_body, m_send, **kwargs):
        """ notifications for finalized bulk jobs should represent the successes and failures of the subjobs """
        m_profile.return_value = {'primary_email': 'icommons-technical@g.harvard.edu'}
        m_bulk_job = get_mock_bulk_job()
        m_bulk_job.get_completed_subjobs_count.return_value = 1
        m_bulk_job.get_failed_subjobs_count.return_value = 2
        self.assertTrue(_send_notification(m_bulk_job))
        m_body.assert_called_once_with(ANY, ANY, 1, 2)

    @patch('canvas_course_site_wizard.management.commands.finalize_bulk_create_jobs._log_notification_failure')
    @patch('canvas_course_site_wizard.management.commands.finalize_bulk_create_jobs.get_canvas_user_profile')
    def test_send_notification_bad_canvas_user(self, m_profile, m_log_failure, **kwargs):
        """ if notification fails due to Canvas user lookup then command should log state and fail gracefully """
        m_profile.side_effect = Exception('problem getting canvas user profile')
        m_bulk_job = get_mock_bulk_job()
        self.assertFalse(_send_notification(m_bulk_job))
        m_log_failure.assert_called_once_with(m_bulk_job)

    @patch('canvas_course_site_wizard.management.commands.finalize_bulk_create_jobs._log_notification_failure')
    @patch('canvas_course_site_wizard.management.commands.finalize_bulk_create_jobs.send_email_helper')
    @patch('canvas_course_site_wizard.management.commands.finalize_bulk_create_jobs._format_notification_email_body')
    @patch('canvas_course_site_wizard.management.commands.finalize_bulk_create_jobs._format_notification_email_subject')
    @patch('canvas_course_site_wizard.management.commands.finalize_bulk_create_jobs.get_canvas_user_profile')
    def test_send_notification_bad_send(self, m_profile, m_subj, m_body, m_send, m_log_failure, **kwargs):
        """ if notification fails due to send mail helper then command should log state and fail gracefully """
        m_profile.return_value = {'primary_email': 'icommons-technical@g.harvard.edu'}
        m_send.side_effect = Exception('problem with send email helper')
        m_bulk_job = get_mock_bulk_job()
        self.assertFalse(_send_notification(m_bulk_job))
        m_log_failure.assert_called_once_with(m_bulk_job)

    def test_format_notification_email_subject(self, **kwargs):
        """ text insertion should work as expected for building email subject """
        subj = _format_notification_email_subject('colgsas', 2)
        self.assertEqual(subj, 'colgsas 2')

    def test_format_notification_email_body(self, **kwargs):
        """ text insertion should work as expected for building email body with no failed subjobs"""
        body = _format_notification_email_body('colgsas', 2, 5, 0)
        self.assertEqual(body, 'colgsas 2 5')

    def test_format_notification_email_body_with_failed_subjobs(self, **kwargs):
        """ text insertion should work as expected for building email body with failed subjobs"""
        body = _format_notification_email_body('colgsas', 2, 5, 1)
        self.assertEqual(body, 'colgsas 2 5 1')
