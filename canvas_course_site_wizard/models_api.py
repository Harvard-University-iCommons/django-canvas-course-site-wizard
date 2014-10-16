from .models import SISCourseData, CanvasContentMigrationJob, CanvasSchoolTemplate

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

