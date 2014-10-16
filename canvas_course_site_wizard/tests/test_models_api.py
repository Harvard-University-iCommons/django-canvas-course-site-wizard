from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.test import TestCase
from canvas_course_site_wizard.models_api import get_template_for_school
from canvas_course_site_wizard.models import CanvasSchoolTemplate


class ModelsApiTest(TestCase):
    longMessage = True

    def setUp(self):
        self.school_id = 'fas'
        self.template_id = 123456

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

    #TODO: once we figure out how to deal with legacy data, we can add integration tests for retrieving course data
