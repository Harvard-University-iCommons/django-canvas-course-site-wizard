from django.core.exceptions import ObjectDoesNotExist
from django.test import TestCase
from canvas_course_site_wizard.models_api import (get_content_migration_data_for_canvas_course_id, 
    get_content_migration_data_for_sis_course_id)
from canvas_course_site_wizard.models import CanvasContentMigrationJob


class ModelsApiTest(TestCase):
    longMessage = True

    def setUp(self):
        self.canvas_course_id = '12'
        self.sis_course_id = '54321'
        self.content_migration_id = '10'
        self.status_url = "canvas_status_url"
        self.workflow_state = "pre_processing"
        self.created_by_user_id = "testuser"

    def test_valid_data_record_returned_given_canvas_course_id(self):
        """ Test that the  method will return valid  migration data  given  a canvas_course_id
         that has a matching row 
        """
        CanvasContentMigrationJob.objects.create(canvas_course_id=self.canvas_course_id,
             sis_course_id=self.sis_course_id, content_migration_id = self.content_migration_id, 
             status_url=self.status_url, created_by_user_id=self.created_by_user_id)
        ret = get_content_migration_data_for_canvas_course_id(self.canvas_course_id)
        self.assertTrue(ret, self)

    def test_that_none_retrurned_when_no_data_for_canvas_course_id(self):
        """ Test that the method will  return None if migration data doens't exist for canvas_course_id """
        ret = get_content_migration_data_for_canvas_course_id(self.canvas_course_id)
        self.assertEqual(ret, None)

    def test_multiple_templates_exist_for_canavas_course_is(self):
        """ Test that the method will  return first matching record if there are multiple records """
        CanvasContentMigrationJob.objects.create(canvas_course_id=self.canvas_course_id,
             sis_course_id=self.sis_course_id, content_migration_id = self.content_migration_id, 
             status_url=self.status_url, created_by_user_id="user1")        
        CanvasContentMigrationJob.objects.create(canvas_course_id=self.canvas_course_id,
             sis_course_id=self.sis_course_id, content_migration_id = self.content_migration_id, 
             status_url=self.status_url, created_by_user_id="user2")
        ret = get_content_migration_data_for_canvas_course_id(self.canvas_course_id)
        self.assertTrue(ret.created_by_user_id,"user1")

    def test_status_url_returned_for_canvas_course_id(self):
        """ Test that the  method will return the status URL given  a canvas_course_id that has a matching row """
        CanvasContentMigrationJob.objects.create(canvas_course_id=self.canvas_course_id,
             sis_course_id=self.sis_course_id, content_migration_id = self.content_migration_id, 
             status_url=self.status_url, created_by_user_id=self.created_by_user_id)
        ret = get_content_migration_data_for_canvas_course_id(self.canvas_course_id)
        self.assertTrue(ret.status_url, self.status_url)

    def test_valid_migration_data_record_returned_given_sis_course_id(self):
        """ Test that the  method will return valid  migration data given a 
        sis_course_id that has a matching row 
        """
        CanvasContentMigrationJob.objects.create(canvas_course_id=self.canvas_course_id,
             sis_course_id=self.sis_course_id, content_migration_id = self.content_migration_id, 
             status_url=self.status_url, created_by_user_id=self.created_by_user_id)
        ret = get_content_migration_data_for_sis_course_id(self.sis_course_id)
        self.assertTrue(ret, self)

    def test_that_none_retrurned_when_no_data_for_sis_course_id(self):
        """ Test that the method will  return None if migration data doens't exist for sis_course_id """
        ret = get_content_migration_data_for_sis_course_id(self.sis_course_id)
        self.assertEqual(ret, None)

    def test_multiple_templates_exist_for_sis_course_is(self):
        """ Test that the method will  return first matching record if there are multiple records """
        CanvasContentMigrationJob.objects.create(canvas_course_id=self.canvas_course_id,
             sis_course_id=self.sis_course_id, content_migration_id = self.content_migration_id, 
             status_url=self.status_url, created_by_user_id="user1")        
        CanvasContentMigrationJob.objects.create(canvas_course_id=self.canvas_course_id,
             sis_course_id=self.sis_course_id, content_migration_id = self.content_migration_id, 
             status_url=self.status_url, created_by_user_id="user2")
        ret = get_content_migration_data_for_sis_course_id(self.sis_course_id)
        self.assertTrue(ret.created_by_user_id,"user1")

    