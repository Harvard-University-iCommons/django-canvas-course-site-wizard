from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.test import TestCase
from canvas_course_site_wizard.models_api import (get_template_for_school, get_courses_for_term, get_bulk_job_records_for_term)
from canvas_course_site_wizard.models import CanvasSchoolTemplate
from setup_bulk_jobs import create_bulk_jobs
from mock import patch

class ModelsApiTest(TestCase):
    longMessage = True

    def setUp(self):
        self.school_id = 'fas'
        self.template_id = 123456
        self.term_id = 4545
        self.bulk_job_id = 999
        create_bulk_jobs(self.term_id, self.bulk_job_id)

    def test_single_template_exists_for_school(self):
        """ Data api method should return the template_id for a given school that has a matching row """
        CanvasSchoolTemplate.objects.create(school_id=self.school_id, template_id=self.template_id)
        res = get_template_for_school(self.school_id)
        self.assertEqual(res, self.template_id)

    def test_single_template_exists_for_another_school(self):
        """
        Data api method should raise an ObjectDoesNotExist exception if no template exists for school,
        even if there are templates that exist for other schools
        """
        CanvasSchoolTemplate.objects.create(school_id='another-school', template_id=self.template_id)
        with self.assertRaises(ObjectDoesNotExist):
            get_template_for_school(self.school_id)

    def test_no_templates_exist_for_school(self):
        """ Data api method should raise an ObjectDoesNotExist exception if no template exists for school """
        with self.assertRaises(ObjectDoesNotExist):
            get_template_for_school(self.school_id)

    def test_multiple_templates_exist_for_school(self):
        """ Data api method should raise a MultipleObjectsReturned exception if > 1 template exists for school """
        CanvasSchoolTemplate.objects.create(school_id=self.school_id, template_id=self.template_id)
        CanvasSchoolTemplate.objects.create(school_id=self.school_id, template_id=self.template_id + 1)

        with self.assertRaises(MultipleObjectsReturned):
            get_template_for_school(self.school_id)

    @patch('canvas_course_site_wizard.models_api.CourseInstance.objects.filter')
    def test_get_courses_for_term_term_id_only(self, mock_ci):
        """ test that the call to the course instance model has the correct parameters when only the term_id is provided """
        courses = get_courses_for_term(self.term_id)
        mock_ci.assert_called_once_with(term__term_id=self.term_id)

    @patch('canvas_course_site_wizard.models_api.CourseInstance.objects.filter')
    def test_get_courses_for_term_term_id_and_status(self, mock_ci):
        """ test that the call to the course instance model has the correct parameters when both term_id and is_in_canvas are provided """
        courses = get_courses_for_term(self.term_id, is_in_canvas=True)
        mock_ci.assert_called_once_with(term__term_id=self.term_id, sync_to_canvas=True)

    def test_get_bulk_job_records_for_term(self):
        """ test that the call to the bulk_job model reutrns the correct results when only the term_id is provided """
        test_data_set = [
            '<BulkCanvasCourseCreationJob: (BulkJob ID=2: sis_term_id=4545)>',
            '<BulkCanvasCourseCreationJob: (BulkJob ID=5: sis_term_id=4545)>',
            '<BulkCanvasCourseCreationJob: (BulkJob ID=3: sis_term_id=4545)>',
            '<BulkCanvasCourseCreationJob: (BulkJob ID=1: sis_term_id=4545)>',
            '<BulkCanvasCourseCreationJob: (BulkJob ID=4: sis_term_id=4545)>',
        ]

        records = get_bulk_job_records_for_term(self.term_id)
        self.assertQuerysetEqual(records, test_data_set, ordered=False)

    def test_get_bulk_job_records_for_term_with_in_progress(self):
        """
        test that the call to the bulk_job model reutrns the correct results when the term_id and in_progress options are provided.
        We should only be returning the jobs that are not in one of the final states ('notification_successful', 'notification_failed')
        """
        test_data_set = [
            '<BulkCanvasCourseCreationJob: (BulkJob ID=1: sis_term_id=4545)>',
            '<BulkCanvasCourseCreationJob: (BulkJob ID=4: sis_term_id=4545)>',
            '<BulkCanvasCourseCreationJob: (BulkJob ID=5: sis_term_id=4545)>',
        ]

        records = get_bulk_job_records_for_term(self.term_id, in_progress=True)
        self.assertQuerysetEqual(records, test_data_set, ordered=False)

    #TODO: once we figure out how to deal with legacy data, we can add integration tests for retrieving course data
