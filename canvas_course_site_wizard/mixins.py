from .models_api import get_course_data
from icommons_common.canvas_utils import SessionInactivityExpirationRC
from canvas_sdk.methods import admins
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.views.generic.detail import SingleObjectMixin
from django.http import Http404
from django.conf import settings
from django.utils.translation import ugettext as _

import logging

# Set up the request context that will be used for canvas API calls
SDK_CONTEXT = SessionInactivityExpirationRC(**settings.CANVAS_SDK_SETTINGS)

logger = logging.getLogger(__name__)


class CourseDataMixin(SingleObjectMixin):
    """
    Retrieve an sis course data object and store in context
    """
    context_object_name = 'course_data'

    def get_object(self, queryset=None):
        """ Retrieve course data object by primary key """
        # Try looking up by primary key.
        pk = self.kwargs.get(self.pk_url_kwarg, None)
        if pk is None:
            raise AttributeError("Course data detail view %s must be called with an object pk."
                                 % self.__class__.__name__)

        try:
            logger.debug("inside get_object of %s about to retrieve course object!" % self.__class__.__name__)
            course_data = get_course_data(pk)
        except ObjectDoesNotExist:
            raise Http404(_("No %s found for the given key %s" % ('course_data', pk)))

        return course_data


class CourseDataPermissionsMixin(CourseDataMixin):
    """
    Provide permission checks for the currently logged in user against an sis course data instance.
    This mixin should be placed after the LoginRequiredMixin
    """

    def is_current_user_member_of_course_staff(self):
        """
        Use the set course_data object primary key to determine if the current user
        is a member of the course staff based on the groups stored in session.

        :return: True or False depending on whether user is in staff list
        :rtype: boolean
        """
        if not self.object:  # Make sure we have the course data
            self.object = self.get_object()

        staff_group = 'ScaleCourseStaff:%s' % self.object.pk
        user_groups = self.request.session.get('USER_GROUPS', [])
        logger.debug("inside CourseDataPermissionMixin - user groups are %s" % user_groups)
        return staff_group in user_groups

    def list_current_user_admin_roles_for_course(self):
        """
        Make an API call to Canvas that returns the list of account admins associated with the course's
        school.  Limit result set to the currently logged in user.  The list can be used for truth testing
        conditions.

        :return: Canvas account admin information (response of admin request)
        :rtype: json list of account admins, limited to current user
        :raises: Exception from SDK
        """
        if not self.object:  # Make sure we have the course data
            self.object = self.get_object()

        # List account admins for school associated with course.  Limit to the sis_user_id, which is
        # equivalent to the currently logged in user's PIN (i.e. their username).
        user_accout_admin_list = admins.list_account_admins(
            request_ctx=SDK_CONTEXT,
            account_id='sis_account_id:school:%s' % self.object.school_code,
            user_id='sis_user_id:%s' % self.request.user.username
        ).json()
        logger.debug("admin list is %s" % user_accout_admin_list)

        return user_accout_admin_list


class CourseSiteCreationAllowedMixin(CourseDataPermissionsMixin):

    """
    Processes permission checks required for initiating course creation.  Being a mixin allows for a
    view to implement multiple mixins that override dispatch.
    """

    def dispatch(self, request, *args, **kwargs):
        # Retrieve the course data object and determine if user can go ahead with creation
        self.object = self.get_object()
        if not (self.is_current_user_member_of_course_staff() or self.list_current_user_admin_roles_for_course()):
            raise PermissionDenied(
                "You must be a member of the course staff or an account admin to perform this action!"
            )
        return super(CourseSiteCreationAllowedMixin, self).dispatch(request, *args, **kwargs)
