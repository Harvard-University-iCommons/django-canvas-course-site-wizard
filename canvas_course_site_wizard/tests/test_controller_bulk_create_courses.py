from unittest import TestCase

from mock import patch, call, ANY
from django.core.exceptions import ObjectDoesNotExist

from canvas_course_site_wizard.controller import setup_bulk_jobs
from canvas_course_site_wizard.models import (CanvasContentMigrationJobProxy,
                                              BulkCanvasCourseCreationJob)


class SetupBulkJobsTest(TestCase):
    longMessage = True

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
        for course in self.courses:
            self.create_course_calls.append(call(course, self.user_id, bulk_job_id=self.bulk_job_id))
            self.course_data_calls.append(call(course))
            self.finalize_calls.append(call(ANY, course, 'sis_user_id:%s' % self.user_id, bulk_job_id=self.bulk_job_id))
            self.template_copy_calls.append(call(ANY, ANY, self.user_id, bulk_job_id=self.bulk_job_id))
        self.job = BulkCanvasCourseCreationJob.objects.create(
                school_id=self.school_code,
                sis_term_id=self.sis_term_id,
                status=BulkCanvasCourseCreationJob.STATUS_SETUP,
                created_by_user_id=self.user_id
            )

    def test_setup_bulk_jobs_create_jobs(self):
        """ Test that setup_bulk_jobs creates the content migration job records """
        setup_bulk_jobs(self.courses, self.user_id, self.job.pk)
        courses = CanvasContentMigrationJobProxy.get_jobs_by_workflow_state(CanvasContentMigrationJobProxy.STATUS_SETUP)
        course_ids = [int(course.sis_course_id) for course in courses ]
        job = BulkCanvasCourseCreationJob.objects.get(pk=self.job.pk)
        self.assertEqual(job.status, BulkCanvasCourseCreationJob.STATUS_PENDING)
        self.assertEquals(self.courses, course_ids)

    @patch('canvas_course_site_wizard.controller.logger.exception')
    @patch('canvas_course_site_wizard.controller.CanvasContentMigrationJob.objects.bulk_create')
    def test_logger_is_called_when_exception_occurs(self, mock_bulk_create, mock_logger):
        """ test that if an exception occures when trying to create the bulk job records the error is logged """
        mock_bulk_create.side_effect = Exception('Error')
        setup_bulk_jobs(self.courses, self.user_id, self.job.pk)
        mock_logger.assert_called_with(ANY)

    @patch('canvas_course_site_wizard.controller.logger.exception')
    @patch('canvas_course_site_wizard.controller.BulkCanvasCourseCreationJob.objects.get')
    @patch('canvas_course_site_wizard.controller.CanvasContentMigrationJob.objects.bulk_create')
    def test_logger_is_called_when_objectdoesnotexist_occurs(self, mock_bulk_create, mock_get, mock_logger):
        """ test that if an exception occures when trying to create the bulk job records the error is logged """
        mock_get.side_effect = ObjectDoesNotExist()
        setup_bulk_jobs(self.courses, self.user_id, self.job.pk)
        mock_logger.assert_called_with(ANY)

