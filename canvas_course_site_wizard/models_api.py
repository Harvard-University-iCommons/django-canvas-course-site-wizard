from .models import (SISCourseData, CanvasContentMigrationJob, CanvasSchoolTemplate, BulkJob)
from icommons_common.models import (CourseInstance, Term)
from django.db.models import Q

def get_course_data(course_sis_id):
    """
    Returns an instance of the SISCourseData class for the given
    course sis id.  Will raise either an ObjectDoesNotExist exception
    if the id does not map to an instance or a MultipleObjectsReturned
    exception if multiple instances match the input id.
    """
    return SISCourseData.objects.select_related('course').get(pk=course_sis_id)

def get_content_migration_data_for_canvas_course_id(canvas_course_id):
    """
    Retrieve the content migration job data given the canvas_course_id.
    Returns the first mathcing record if it exists or None if it  does not have a job associated.
    """
    result = CanvasContentMigrationJob.objects.filter(canvas_course_id=canvas_course_id)
    if len(result) > 0: 
    	return result[0]
    else:
		return None

def get_content_migration_data_for_sis_course_id(sis_course_id):
    """
    Retrieve the content migration job data given the sis_course_id.
    Returns the first mathcing record if it exists or None if it  does not have a job associated.
    """
    result = CanvasContentMigrationJob.objects.filter(sis_course_id=sis_course_id)
    if len(result) > 0: 
    	return result[0]
    else:
		return None

def get_template_for_school(school_code):
    """
    Retrieve a single course template id for the given school code.  An
    ObjectDoesNotExist exception will be raised if the school does not have a template.
    If there are multiple templates for the school, a MultipleObjectsReturned exception
    will be thrown.
    """
    return CanvasSchoolTemplate.objects.get(school_id=school_code).template_id

def get_courses_for_term(term_id, is_in_canvas=None):
    """
    Get the count of all the courses in the term. If is_in_canvas is true, only get
    the count of the courses that are already in canvas by looking to see if the sync_to_canvas flaf is
    set to true in the course manager database.
    :param term_id: the term_id of the term
    :param is_in_canvas: (optional) if provided the method will only return a count of the courses that already exist in Canvas
    :return: The method returns a count of the number of courses, if no courses are found the method will return 0.
    """
    kwargs = dict()
    kwargs['term__term_id'] = term_id
    if is_in_canvas:
        kwargs['sync_to_canvas'] = True

    return CourseInstance.objects.filter(**kwargs).count()

def get_bulk_job_records_for_term(term_id, in_progress=None):
    """
    Get the bulk job records from the BulkJob table for the sis_term_id provided where in_progress is true.
    """
    term_id_query = Q(sis_term_id=term_id)
    if in_progress:
        status_list = [BulkJob.STATUS_SETUP, BulkJob.STATUS_PENDING, BulkJob.STATUS_FINALIZING]
        return BulkJob.objects.filter(sis_term_id=term_id, status__in=status_list)

    return BulkJob.objects.filter(term_id_query)
