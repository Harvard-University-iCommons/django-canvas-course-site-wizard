from .models import (SISCourseData, CanvasContentMigrationJob, CanvasSchoolTemplate, BulkCanvasCourseCreationJob)
from icommons_common.models import (CourseInstance, Term)


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


def get_courses_for_term(term_id, is_in_canvas=None, is_in_isite=None, not_created=None):
    """
    Get the count of all the courses in the term. If is_in_canvas is true, only get
    the count of the courses that are already in canvas by looking to see if the sync_to_canvas flag is
    set to true in the course manager database.
    :param term_id: the term_id of the term
    :param is_in_canvas: (optional) if provided the method will only return a count of the courses that already exist in Canvas
    :param is_in_isite: (optional) select courses that have isites
    :return: The method returns a count of the number of courses, if no courses are found the method will return 0.
    """
    kwargs = { 'term__term_id' : term_id }

    if is_in_canvas:
        kwargs['sync_to_canvas'] = True

    if is_in_isite:
        kwargs['sites__site_type_id'] = 'isite'

    if not_created:
        kwargs['sites__external_id__isnull'] = True

    return CourseInstance.objects.filter(**kwargs).count()


def get_bulk_job_records_for_term(term_id, in_progress=None):
    """
    Get the bulk job records from the BulkCanvasCourseCreationJob table for the sis_term_id.
    if in_progress is true, get only those jobs that have an active status.
    """

    kwargs = { 'sis_term_id' : term_id }
    if in_progress:
        status_list = [BulkCanvasCourseCreationJob.STATUS_SETUP,
                       BulkCanvasCourseCreationJob.STATUS_PENDING,
                       BulkCanvasCourseCreationJob.STATUS_FINALIZING]
        kwargs['status__in'] = status_list

    return BulkCanvasCourseCreationJob.objects.filter(**kwargs)

def select_courses_for_bulk_create(term_id):
    """
    Given a term id, select all course instance id's that are eligible to have a Canvas
    course created. The statement below selects courses where:
        term_id = term_is
        external_id = Null
        site_type_id != 'isite'

    :param term_id:
    :return: List of course instance id's
    """
    select_query = {
        'term_id': term_id,
        'sites__external_id__isnull': True,
        }

    exclude_query = {
        'sites__site_type_id': 'isite',
        }

    return CourseInstance.objects.filter(**select_query)\
        .exclude(**exclude_query).values_list('course_instance_id', flat=True)
