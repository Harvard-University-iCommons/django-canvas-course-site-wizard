from .models_api import get_course_data, get_template_for_school
from .models import CanvasContentMigrationJob, SISCourseData
from .exceptions import NoTemplateExistsForSchool, NoCanvasUserToEnroll
from canvas_sdk.methods.courses import create_new_course
from canvas_sdk.methods.sections import create_course_section
from canvas_sdk.methods.enrollments import enroll_user_sections
from canvas_sdk.methods.users import get_user_profile
from canvas_sdk.methods import content_migrations
from django.conf import settings
from django.http import Http404
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail
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
    try:
        request_parameters = dict(request_ctx=SDK_CONTEXT,
                account_id = 'sis_account_id:' + course_data.sis_account_id,
                course_name = course_data.course_name,
                course_course_code = course_data.course_code,
                course_term_id = 'sis_term_id:' + course_data.sis_term_id,
                course_sis_course_id= sis_course_id)
        new_course = create_new_course(**request_parameters).json()
        logger.info("created  course object, ret=%s" % (new_course))
    except Exception as e:
        logger.error('Error creating new Canvas course with request=%s: %s' % (request_parameters, e))
        raise

    # 3. Create course section after course  creation
    try:
        section = create_course_section(
                    SDK_CONTEXT,
                    course_id = new_course['id'],
                    course_section_name = course_data.primary_section_name(),
                    course_section_sis_section_id = sis_course_id
                    )
        logger.info("created section= %s" %(section.json()))
    except Exception as e:
        logger.error('Error creating default section for Canvas course with new_course.request=%s and response=%s: %s'
                     % (new_course.request, new_course.json(), e))
        raise

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


def finalize_new_canvas_course(canvas_course_id, sis_course_id, user_id):
    """
    Performs all synchronous tasks required to initialize a new canvas course after the course template
    has been applied, or after checking for a template if the course has no template.

        :param canvas_course_id: newly created Canvas course ID; used to build course URL
        :type canvas_course_id: string
        :param sis_course_id: newly created Canvas course SIS ID; used to enroll course creator
        :type sis_course_id: string
        :param user_id: The user ID of the creator/instructor to enroll in the course; this should be
        either the Canvas user ID or the SIS user ID prepended with the string 'sis_user_id:'
        :type user_id: string
        :raises: Logs and re-raises various exceptions raised by its component processes
    """

    # Enroll instructor / creator
    try:
        enrollment = enroll_creator_in_new_course(sis_course_id, user_id)
        logger.info('Enrolled user_id=%s in new course with Canvas course id=%s' % (user_id, canvas_course_id))
        logger.debug("enrollment result: %s" % enrollment)
    except Exception as e:
        logger.error('Error enrolling course creator with user_id=%s in new course with Canvas course id=%s: %s'
                     % (user_id, canvas_course_id, e))
        raise

    # Copy SIS enrollments to new Canvas course
    try:
        sis_course_data = get_course_data(sis_course_id)
        logger.debug("sis_course_data=%s" % sis_course_data)
        sis_course_data = sis_course_data.set_sync_to_canvas(SISCourseData.TURN_ON_SYNC_TO_CANVAS)
        logger.info('Set SIS enrollment data sync flag for new course with Canvas ID=%s' % canvas_course_id)
        logger.debug("sis_course_data after sync to canvas: %s" % sis_course_data)
    except Exception as e:
        logger.error('Error setting SIS enrollment data sync flag for new course with Canvas ID=%s: %s'
                     % (canvas_course_id, e))
        raise

    # Mark course as official
    try:
        canvas_course_url = get_canvas_course_url(canvas_course_id=canvas_course_id)
        site_map = sis_course_data.set_official_course_site_url(canvas_course_url)
        logger.info('Marked new course with Canvas ID=%s as official' % canvas_course_id)
        logger.debug("site_map: %s" % site_map)
    except Exception as e:
        logger.error('Error marking new course with Canvas ID=%s as official: %s' % (canvas_course_id, e))
        raise

    logger.info("All tasks for finalizing new course with Canvas ID=%s completed." % canvas_course_id)

    return canvas_course_url


def enroll_creator_in_new_course(sis_course_id, user_id):
    """
    Silently enroll instructor / creator to the new course so it can be accessed immediately

        :param course: newly created Canvas course object to enroll course creator
        :type course: SDK response of create_new_course from canvas_sdk.methods.courses
                      (JSON dictionary representation of a Canvas course)
        :param sis_user_id: The SIS user ID of the creator/instructor to enroll in the course
        :type sis_user_id: string
        :return: Canvas enrollment information (response of enrollment request)
        :rtype: requests.Response
        :raises: NoCanvasUserToEnroll
    """

    # check if user exists in Canvas before enrolling
    logger.debug("Checking for user_id=%s" % user_id)

    get_user_response = get_user_profile(request_ctx=SDK_CONTEXT, user_id=user_id)

    logger.debug("--> response: %s" % get_user_response.json())

    if get_user_response.status_code == 200:
        # user was found; we may have found user using sis_user_id, so make sure we note canvas_user_id from response
        user_data = get_user_response.json()
        canvas_user_id = str(user_data['id'])
    else:
        # Could not find user matching sis_user_id
        logger.debug("No user found with user_id=%s" % user_id)
        raise NoCanvasUserToEnroll(user_id)

    # Assumptions:
    # 1. the course creator should be enrolled in a section with sis_section_id equal to the SIS course ID
    # 2. the course creator should be enrolled as a teacher
    current_user_enrollment_result = enroll_user_sections(request_ctx=SDK_CONTEXT,
                                                          section_id='sis_section_id:%s' % sis_course_id,
                                                          enrollment_user_id=canvas_user_id,
                                                          enrollment_type='TeacherEnrollment',
                                                          enrollment_enrollment_state='active')

    logger.debug("Enroll user response: %s" % current_user_enrollment_result.json())

    return current_user_enrollment_result.json()

def get_canvas_user_profile(sis_user_id):
    """
    This method will fetch the canvas user profile , given the sis_user_id
    :param canvas_user_id: The sis_user_id of the user, without the sis_user_id: prefix
    :type canvas_user_id: string
    return: Returns json representing the canvas user profile fetched by the canvas_sdk
    """
    response = get_user_profile(request_ctx=SDK_CONTEXT, user_id='sis_user_id:%s' % sis_user_id)
    canvas_user_profile = response.json()
    return canvas_user_profile

def send_email_helper(subject, message, to_address):
    """
    This is a helper method to send email using django's mail module. The mail is sent
    to the specified receipients using the subject and body provided. The 'from' address
     is obtained from the settings file. 
    :param subject: The subject for the email, a String 
    :param message: The body of the email, a String 
    :param to_address: The list of recepients, a list of Strings 
    """
    from_address = settings.CANVAS_EMAIL_NOTIFICATION['from_email_address']
    logger.debug("==>Within send email: from_addr=%s, to_addr=%s" % (from_address, to_address))
    # If fail_silently is set to False, send_mail will raise exceptions. If True,
    # all exceptions raised while sending the message will be quashed.
    send_mail(subject, message, from_address, to_address, fail_silently=False)
        
def get_canvas_course_url(canvas_course_id=None, sis_course_id=None, override_base_url=None):
    """
    This utility method formats a Canvas course URL string which will point to the course home page in Canvas. It
     relies on CANVAS_SITE_SETTINGS['base_url'] as a default. This utility method does not check the validity of the
     input arguments (it will build a string from whatever input it is given, including bad input from settings).

     This method may eventually be in the Canvas Python SDK -- if so, the test should go with it and we might consider
     some argument validation.

    :param canvas_course_id: The ID canvas uses for the course. This will be used if provided, even if sis_course_id
    is also provided; in other words, this value takes precedence over sis_course_id.
    :param sis_course_id: The SIS course ID
    :param override_base_url: The fully qualified base URL for a Canvas server, including http(s)://, domain, and
    trailing forward slash.
    :return: Method returns a URL for a given Canvas course which will point to the course home page in Canvas.
    """

    if canvas_course_id is not None:
        course_id = canvas_course_id
    elif sis_course_id is not None:
        course_id = "sis_course_id:%s" % sis_course_id
    else:
        return None

    if override_base_url is not None:
        base_url = override_base_url
    else:
        base_url = settings.CANVAS_SITE_SETTINGS['base_url']

    course_url = '%scourses/%s' % (base_url, course_id)

    return course_url
