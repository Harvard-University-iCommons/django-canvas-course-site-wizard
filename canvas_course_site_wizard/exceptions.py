from icommons_ui.exceptions import RenderableException
from django.conf import settings


class NoTemplateExistsForSchool(Exception):
    def __init__(self, school_id):
        self.school_id = school_id

    def __unicode__(self):
        return u'No template exists for school_id=%s' % self.school_id

    def __str__(self):
        return 'No template exists for school_id=%s' % self.school_id


class NoCanvasUserToEnroll(RenderableException):
    def __init__(self, user_id, *args, **kw_args):
        super(NoCanvasUserToEnroll, self).__init__(self, *args, **kw_args)
        self._user_id = user_id
        # Do not display any additional information about the Canvas user not existing directly to the user;
        # handle this as a failure to enroll the creator. Logs will capture the exact issue.
        self._display_text = settings.COURSE_WIZARD_CUSTOM_ERRORS['enroll_creator']
        self._status_code = 404  # Canvas user not found


class CanvasEnrollmentError(RenderableException):
    def __init__(self, course_id, *args, **kw_args):
        super(CanvasEnrollmentError, self).__init__(self, *args, **kw_args)
        self._course_id = course_id
        self._display_text = settings.COURSE_WIZARD_CUSTOM_ERRORS['enroll_creator']


class CopySISEnrollmentsError(RenderableException):
    def __init__(self, *args, **kw_args):
        super(CopySISEnrollmentsError, self).__init__(self, *args, **kw_args)
        self._display_text = settings.COURSE_WIZARD_CUSTOM_ERRORS['copy_sis_enrollments']


class MarkOfficialError(RenderableException):
    def __init__(self, *args, **kw_args):
        super(MarkOfficialError, self).__init__(self, *args, **kw_args)
        self._display_text = settings.COURSE_WIZARD_CUSTOM_ERRORS['mark_official']


class CanvasCourseCreateError(RenderableException):
    def __init__(self, sis_course_id, *args, **kw_args):
        super(CanvasCourseCreateError, self).__init__(self, *args, **kw_args)
        self._sis_course_id = sis_course_id
        self._display_text = settings.COURSE_WIZARD_CUSTOM_ERRORS['canvas_course_create'].format(sis_course_id)


class CanvasCourseAlreadyExists(CanvasCourseCreateError):
    def __init__(self, sis_course_id, *args, **kw_args):
        super(CanvasCourseAlreadyExists, self).__init__(self, sis_course_id, *args, **kw_args)
        self._display_text = settings.COURSE_WIZARD_CUSTOM_ERRORS['canvas_course_already_exists'].format(sis_course_id)
        self._status_code = 400  # Course already exists; bad request


class CanvasSectionCreateError(RenderableException):
    def __init__(self, sis_course_id, *args, **kw_args):
        super(CanvasSectionCreateError, self).__init__(self, *args, **kw_args)
        self._sis_course_id = sis_course_id
        self._display_text = settings.COURSE_WIZARD_CUSTOM_ERRORS['canvas_section_create'].format(sis_course_id)


class CanvasSectionAlreadyExists(CanvasSectionCreateError):
    def __init__(self, sis_course_id, *args, **kw_args):
        super(CanvasSectionAlreadyExists, self).__init__(self, sis_course_id, *args, **kw_args)
        self._display_text = settings.COURSE_WIZARD_CUSTOM_ERRORS['canvas_section_already_exists'].format(sis_course_id)
        self._status_code = 400  # Section already exists; bad request


class SISCourseInfoError(RenderableException):
    def __init__(self, sis_course_id, *args, **kw_args):
        super(SISCourseInfoError, self).__init__(self, *args, **kw_args)
        self._sis_course_id = sis_course_id
        self._display_text = settings.COURSE_WIZARD_CUSTOM_ERRORS['sis_course_info'].format(sis_course_id)


class SISCourseDoesNotExistError(SISCourseInfoError):
    def __init__(self, sis_course_id, *args, **kw_args):
        super(SISCourseDoesNotExistError, self).__init__(self, sis_course_id, *args, **kw_args)
        self._display_text = settings.COURSE_WIZARD_CUSTOM_ERRORS['sis_course_does_not_exist'].format(sis_course_id)
        self._status_code = 404  # Canvas user not found

