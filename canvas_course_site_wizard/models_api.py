import logging

from .models import (
    SISCourseData,
    CanvasCourseGenerationJob,
    CanvasSchoolTemplate,
)

logger = logging.getLogger(__name__)


def get_course_data(course_sis_id):
    """
    Returns an instance of the SISCourseData class for the given
    course sis id.  Will raise either an ObjectDoesNotExist exception
    if the id does not map to an instance or a MultipleObjectsReturned
    exception if multiple instances match the input id.
    """
    return SISCourseData.objects.select_related('course').get(pk=course_sis_id)


def get_course_generation_data_for_canvas_course_id(canvas_course_id):
    """
    Retrieve the Canvas course generation job data given the canvas_course_id.
    Returns the first matching record if it exists or None if it does not have
    a job associated.
    """
    result = CanvasCourseGenerationJob.objects.filter(
        canvas_course_id=canvas_course_id
    )
    if len(result) > 0:
        return result[0]
    else:
        return None


def get_course_generation_data_for_sis_course_id(sis_course_id,
                                                 course_job_id=None,
                                                 bulk_job_id=None):
    """
    Retrieve the Canvas course generation job data given the sis_course_id and
    an optional bulk_job_id.
    Returns the first matching record if it exists or None if it  does not have
    a job associated.
    """
    kwargs = {'sis_course_id': sis_course_id, }
    # if there is a job id, there's no need for any other params
    if course_job_id:
        kwargs['pk'] = course_job_id
    else:
        # if there was no job_id, see if there's a bulk_job_id
        # if not, query for bulk_job_id is null
        if bulk_job_id:
            kwargs['bulk_job_id'] = bulk_job_id
        else:
            kwargs['bulk_job_id__isnull'] = True

    try:
        return CanvasCourseGenerationJob.objects.get(**kwargs)
    except (CanvasCourseGenerationJob.DoesNotExist,
            CanvasCourseGenerationJob.MultipleObjectsReturned) as e:
        logger.exception(
            'Unable to find single CanvasCourseGenerationJob for sis_course_id '
            '{}, course_job_id {}, bulk_job_id {}'.format(
                sis_course_id, course_job_id, bulk_job_id))
        return None


def get_template_for_school(school_code):
    """
    Retrieve a single course template id for the given school code.  An
    ObjectDoesNotExist exception will be raised if the school does not have a template.
    If there are multiple templates for the school, a MultipleObjectsReturned exception
    will be thrown.
    """
    return CanvasSchoolTemplate.objects.get(school_id=school_code).template_id
