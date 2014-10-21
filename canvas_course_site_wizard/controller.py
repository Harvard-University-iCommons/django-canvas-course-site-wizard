from .models_api import get_course_data, get_template_for_school
from .models import CanvasContentMigrationJob
from .exceptions import NoTemplateExistsForSchool, NoCanvasUserToEnroll, TooManyMatchingUsersToEnroll
from canvas_sdk.methods.courses import create_new_course
from canvas_sdk.methods.sections import create_course_section
from canvas_sdk.methods.enrollments import enroll_user_sections
from canvas_sdk.methods.users import list_users_in_account
from canvas_sdk.methods import content_migrations
from json import loads
from django.conf import settings
from django.http import Http404
from django.core.exceptions import ObjectDoesNotExist
from icommons_common.canvas_utils import SessionInactivityExpirationRC

import logging

# Set up the request context that will be used for canvas API calls
SDK_CONTEXT = SessionInactivityExpirationRC(**settings.CANVAS_SDK_SETTINGS)
logger = logging.getLogger(__name__)


def create_canvas_course(sis_course_id):
    """This method creates a canvas course for the  sis_course_id provided."""

    new_course = None
    try:
        #1. fetch the course instance info 
        course_data = get_course_data(sis_course_id)

        logger.info("\n obtained  course info for ci=%s, acct_id=%s, course_name=%s, code=%s, term=%s, section_name=%s\n"
         %(course_data,course_data.sis_account_id, course_data.course_name, course_data.course_code, course_data.sis_term_id,course_data.primary_section_name() ))
    except ObjectDoesNotExist as e:
        logger.error('ObjectDoesNotExist  exception in  create course:  %s, exception=%s' % (sis_course_id, e))
        raise Http404

    #2. Create canvas course
    new_course = create_new_course(SDK_CONTEXT,
            account_id = 'sis_account_id:' + course_data.sis_account_id,
            course_name = course_data.course_name,
            course_course_code = course_data.course_code,
            course_term_id = 'sis_term_id:' + course_data.sis_term_id,
            course_sis_course_id= sis_course_id).json()
    logger.info("created  course object, ret=%s" % (new_course))

    # 3. Create course section after course  creation
    section = create_course_section(
                SDK_CONTEXT, 
                course_id = new_course['id'],
                course_section_name = course_data.primary_section_name(),
                course_section_sis_section_id = sis_course_id
                )
    logger.info("created section= %s" %(section.json()))

    return new_course


def start_course_template_copy(sis_course, canvas_course_id, user_id):
    """
    This method will retrieve the template site associated with an SISCourseData object and start the
    Canvas process of copying the template content into the canvas course site.  A CanvasContentMigrationJob
    row will be created with the async process data from Canvas and the resulting data object will be
    returned.  If the school associated with the sis data object does not have a template, a
    NoTemplateExistsForSchool exception will be raised.
    """

    try:
        template_id = get_template_for_school(sis_course.school_code)
    except ObjectDoesNotExist:
        raise NoTemplateExistsForSchool(sis_course.school_code)

    # Initiate course copy for template_id
    content_migration = content_migrations.create_content_migration_courses(
        SDK_CONTEXT,
        canvas_course_id,
        migration_type='course_copy_importer',
        settings_source_course_id=template_id,
    ).json()

    # Return newly created content_migration_job row that contains progress url
    return CanvasContentMigrationJob.objects.create(
        canvas_course_id=canvas_course_id,
        sis_course_id=sis_course.pk,
        content_migration_id=content_migration['id'],
        status_url=content_migration['progress_url'],
        created_by_user_id=user_id,
    )


def finalize_new_canvas_course(course, sis_user_id):
    """
    Performs all synchronous tasks required to initialize a new canvas course after the course template
    has been applied, or after checking for a template if the course has no template.
        :param course: newly created Canvas course object to enroll course creator
        :type course: SDK response of create_new_course from canvas_sdk.methods.courses
                      (JSON dictionary representation of a Canvas course)
        :param sis_user_id: The SIS user ID of the creator/instructor to enroll in the course
        :type sis_user_id: string
    """

    # Enroll instructor / creator
    try:
        enrollment = enroll_creator_in_new_course(course, sis_user_id)
    except (NoCanvasUserToEnroll, TooManyMatchingUsersToEnroll) as e:
        logger.warn('Error when attempting to enroll sis_user_id=%s in new course with Canvas ID=%s: %s'
                    % (sis_user_id, course['id'], e))

    # TODO: Copy SIS enrollments to new Canvas course

    # TODO: Mark course as official

    logger.info("All tasks for finalizing new course with Canvas ID=%s completed." % course['id'])


def enroll_creator_in_new_course(course, sis_user_id):
    """
    Silently enroll instructor / creator to the new course so it can be accessed immediately

        :param course: newly created Canvas course object to enroll course creator
        :type course: SDK response of create_new_course from canvas_sdk.methods.courses
                      (JSON dictionary representation of a Canvas course)
        :param sis_user_id: The SIS user ID of the creator/instructor to enroll in the course
        :type sis_user_id: string
        :return: Canvas enrollment information (response of enrollment request)
        :rtype: requests.Response
        :raises: NoCanvasUserToEnroll, TooManyMatchingUsersToEnroll
    """

    # check if user exists in Canvas before enrolling
    logger.debug("Checking for sis_user_id=%s in account_id=%s" % (sis_user_id, course['account_id']))

    get_user_response = list_users_in_account(request_ctx=SDK_CONTEXT,
                                              account_id=str(course['account_id']),
                                              search_term=str(sis_user_id))

    logger.debug("--> response: %s" % get_user_response.json())

    matching_user_list = get_user_response.json()
    if len(matching_user_list) == 1:
        canvas_user_sis_user_id = matching_user_list[0]['sis_user_id']
    elif len(matching_user_list) == 0:
        # Could not find user matching sis_user_id, log and abort enroll process
        raise NoCanvasUserToEnroll(sis_user_id, course['account_id'])
    else:
        # More than one user matching sis_user_id, log and abort enroll process
        raise TooManyMatchingUsersToEnroll(sis_user_id, course['account_id'])

    # Assumptions:
    # 1. the course creator should be enrolled in a section with sis_section_id equal to the SIS course ID
    # 2. the course creator should be enrolled as a teacher
    current_user_enrollment_result = enroll_user_sections(request_ctx=SDK_CONTEXT,
                                                          section_id='sis_section_id:%s' % course['sis_course_id'],
                                                          enrollment_user_id='sis_user_id:%s' % canvas_user_sis_user_id,
                                                          enrollment_type='TeacherEnrollment',
                                                          enrollment_enrollment_state='active')

    logger.debug("Enroll user response: %s" % current_user_enrollment_result.json())

    return current_user_enrollment_result.json()