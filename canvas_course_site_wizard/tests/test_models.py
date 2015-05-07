from datetime import datetime
from itertools import count
from unittest import TestCase
from mock import patch, Mock
from canvas_course_site_wizard.models import (
    BulkCanvasCourseCreationJobProxy as BulkJob,
    CanvasContentMigrationJob as SubJob
)


def _create_bulk_job(bulk_job_id, sis_term_id=1, status=BulkJob.STATUS_SETUP):
    return BulkJob.objects.create(
        bulk_job_id=bulk_job_id,
        sis_term_id=sis_term_id,
        status=status
    )


def _create_subjob(content_migration_id, canvas_course_id=1, sis_course_id='1',
                   workflow_state=SubJob.STATUS_SETUP, bulk_job_id=1):
    return SubJob.objects.create(
        content_migration_id=content_migration_id,
        canvas_course_id=canvas_course_id,
        sis_course_id=sis_course_id,
        workflow_state=workflow_state,
        bulk_job_id=bulk_job_id
    )


class BulkCanvasCourseCreationJobProxyIntegrationTests(TestCase):

    @classmethod
    def setUpClass(cls):
        """
        Fixture data:
        - one bulk create job of each status, with a subjob of each subjob status type for each bulk job
        - one extra pending bulk create job which is ready to be finalized
        """
        BulkJob.objects.all().delete()
        SubJob.objects.all().delete()
        sub_id_generator = count(1)
        for index, (status, _) in enumerate(BulkJob.STATUS_CHOICES):
            _create_bulk_job(index, status=status)
            for subjob_status, _ in SubJob.WORKFLOW_STATUS_CHOICES:
                _create_subjob(sub_id_generator.next(), workflow_state=subjob_status, bulk_job_id=index)

    @classmethod
    def tearDownClass(cls):
        """ Clear fixture data """
        BulkJob.objects.all().delete()
        SubJob.objects.all().delete()

    def test_get_long_running_jobs_integration(self):
        """ get_long_running_jobs() should return jobs older than a certain threshold age """
        expecting_all_jobs = BulkJob.get_long_running_jobs(older_than_minutes=0)
        expecting_no_jobs = BulkJob.get_long_running_jobs(older_than_minutes=1000)
        self.assertEqual(len(expecting_no_jobs), 0)
        # Based on fixture data, expecting one job in each 'intermediate state' (non-terminal state)
        self.assertEqual(len(expecting_all_jobs), 3)

    def test_get_long_running_jobs_older_than_date(self):
        """ get_long_running_jobs() should return jobs older than a certain threshold datetime """
        expecting_no_jobs = BulkJob.get_long_running_jobs(older_than_date=datetime(1900, 1, 1))
        expecting_all_jobs = BulkJob.get_long_running_jobs(older_than_date=datetime.now())
        self.assertEqual(len(expecting_no_jobs), 0)
        # Based on fixture data, expecting one job in each 'intermediate state' (non-terminal state)
        self.assertEqual(len(expecting_all_jobs), 3)

    def test_get_long_running_jobs_no_arguments(self):
        """ get_long_running_jobs() should raise error if no threshold is specified """
        with self.assertRaises(ValueError):
            BulkJob.get_long_running_jobs()

    def test_get_long_running_jobs_too_many_arguments(self):
        """ get_long_running_jobs() should raise error if multiple thresholds are specified """
        with self.assertRaises(ValueError):
            BulkJob.get_long_running_jobs(older_than_minutes=0, older_than_date=datetime.now())

    def test_get_completed_subjobs_integration(self):
        """ get_completed_subjobs() should only show successfully terminated subjobs for the specified bulk job """
        bulk_job = BulkJob.objects.get(status=BulkJob.STATUS_FINALIZING)
        self.assertEqual(len(bulk_job.get_completed_subjobs()), 1)
        self.assertEqual(bulk_job.get_completed_subjobs_count(), 1)

    def test_get_failed_subjobs_integration(self):
        """ get_failed_subjobs() should only show unsuccessfully terminated subjobs for the specified bulk job """
        job = BulkJob.objects.get(status=BulkJob.STATUS_FINALIZING)
        self.assertEqual(len(job.get_failed_subjobs()), 3)
        self.assertEqual(job.get_failed_subjobs_count(), 3)

    def test_ready_to_finalize_integration_not_ready(self):
        """ bulk jobs not in pending state or with non-terminal subjobs should not be designated as finalizable """
        job_not_pending = BulkJob.objects.get(status=BulkJob.STATUS_SETUP)
        # should have subjobs in non-terminal states based on fixture data, so ready_to_finalize() should fail
        job_pending_but_not_ready = BulkJob.objects.get(status=BulkJob.STATUS_PENDING)
        self.assertFalse(job_not_pending.ready_to_finalize())
        self.assertFalse(job_pending_but_not_ready.ready_to_finalize())

    def test_ready_to_finalize_integration_ready(self):
        """ a bulk job in pending state with terminal subjobs should be designated as finalizable """
        # explicitly set up a pending bulk job for which all subjobs are in a terminal state
        job_pending_and_ready = _create_bulk_job(999, status=BulkJob.STATUS_PENDING)
        subjob_finalized = _create_subjob(9999, workflow_state=SubJob.STATUS_FINALIZED, bulk_job_id=999)
        subjob_finalize_failed = _create_subjob(9999, workflow_state=SubJob.STATUS_FINALIZE_FAILED, bulk_job_id=999)
        subjob_setup_failed = _create_subjob(9999, workflow_state=SubJob.STATUS_SETUP_FAILED, bulk_job_id=999)
        self.assertTrue(job_pending_and_ready.ready_to_finalize())
        # clean up
        job_pending_and_ready.delete()
        subjob_finalized.delete()
        subjob_finalize_failed.delete()
        subjob_setup_failed.delete()


class BulkCanvasCourseCreationJobProxyTests(TestCase):

    @patch('canvas_course_site_wizard.models.BulkCanvasCourseCreationJobProxy.save')
    def test_update_status_success(self, m_save):
        """ If no exception is raised in the save() call then the function should return True (indicating success) """
        job = BulkJob()
        result = job.update_status(BulkJob.STATUS_SETUP)
        self.assertTrue(m_save.called)
        self.assertTrue(result)

    @patch('canvas_course_site_wizard.models.BulkCanvasCourseCreationJobProxy.save')
    def test_update_status_fail_raise(self, m_save):
        """ If raise_exception is True, an exception in the save() call should bubble up """
        result = None
        job = BulkJob()
        m_save.side_effect = Exception
        with self.assertRaises(Exception):
            result = job.update_status(BulkJob.STATUS_SETUP, raise_exception=True)
        self.assertTrue(m_save.called)
        self.assertIsNone(result)

    @patch('canvas_course_site_wizard.models.BulkCanvasCourseCreationJobProxy.save')
    def test_update_status_fail_gracefully(self, m_save):
        """
        If raise_exception is not provided, or is False, an exception in the save() call should not bubble up,
         and the function should return False (indicating failure)
        """
        job = BulkJob()
        m_save.side_effect = Exception
        result = job.update_status(BulkJob.STATUS_SETUP)
        self.assertTrue(m_save.called)
        self.assertFalse(result)
