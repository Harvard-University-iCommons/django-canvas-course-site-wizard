from .models import SISCourseData, CanvasContentMigrationJob


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
    An ObjectDoesNotExist exception will be raised if the canvas_course_id does
    not have a job associated with it.
    """
    return CanvasContentMigrationJob.objects.get(canvas_course_id=canvas_course_id)

def get_content_migration_data_for_sis_course_id(sis_course_id):
    """
    Retrieve the content migration job data given the sis_course_id.
    An ObjectDoesNotExist exception will be raised if the sis_course_id does
    not have a job associated with it.
    """
    return CanvasContentMigrationJob.objects.get(sis_course_id=sis_course_id)


   