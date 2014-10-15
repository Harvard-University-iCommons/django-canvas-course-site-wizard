from .models_api import get_course_data
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.views.generic.detail import SingleObjectMixin
from django.http import Http404
from django.utils.translation import ugettext as _


class CourseDataMixin(SingleObjectMixin):
    """
    Retrieve a course data object based on primary key.
    """
    context_object_name = 'course_data'

    def is_current_user_member_of_course_staff(self, request):
        """
        Use the course_data object primary key to determine if the current user
        is a member of the course staff based on the groups stored in session.
        """
        pk = self.kwargs.get(self.pk_url_kwarg, None)
        if pk is None:
            raise AttributeError("Course data detail view %s must be called with an object pk."
                                 % self.__class__.__name__)

        staff_group = 'ScaleCourseStaff:%s' % pk
        user_groups = request.session.get('USER_GROUPS', [])
        print "user groups are %s" % user_groups
        return staff_group in user_groups

    def get_object(self, queryset=None):
        """ Retrieve course data object by primary key """
        # Try looking up by primary key.
        pk = self.kwargs.get(self.pk_url_kwarg, None)
        if pk is None:
            raise AttributeError("Course data detail view %s must be called with an object pk."
                                 % self.__class__.__name__)

        try:
            course_data = get_course_data(pk)
        except ObjectDoesNotExist:
            raise Http404(_("No %s found for the given key %s" % ('course_data', pk)))

        return course_data


class CourseSiteCreationAllowedMixin(CourseDataMixin):
    """
    Processes permission checks required for initiating course creation.  Being a mixin allows for a
    view to implement multiple mixins that override dispatch.
    """
    def dispatch(self, request, *args, **kwargs):
        # Retrieve the course data object and determine if user can go ahead with creation
        self.object = self.get_object()
        # if not self.is_current_user_member_of_course_staff(request):
        #     raise PermissionDenied
        return super(CourseSiteCreationAllowedMixin, self).dispatch(request, *args, **kwargs)
