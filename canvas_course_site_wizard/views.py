from .controller import create_canvas_course, start_course_template_copy, finalize_new_canvas_course
from .mixins import CourseSiteCreationAllowedMixin
from .exceptions import NoTemplateExistsForSchool
from django.conf import settings
from braces.views import LoginRequiredMixin
from django.views.generic.base import TemplateView
from django.shortcuts import redirect
import logging

logger = logging.getLogger(__name__)


class CanvasCourseSiteCreateView(LoginRequiredMixin, CourseSiteCreationAllowedMixin, TemplateView):
    """
    Serves up the canvas course site creation wizard on GET and creates the
    course site on POST.
    """
    template_name = "canvas_course_site_wizard/canvas_wizard.html"

    def post(self, request, *args, **kwargs):
        course = create_canvas_course(self.object.pk)
        try:
            migration_job = start_course_template_copy(self.object, course['id'])
            # Temporary redirect based on newly created course id, will eventually be async job id
            return redirect('ccsw-status', migration_job)
        except NoTemplateExistsForSchool:
            # If there is no template to copy, immediately finalize the new course
            # (i.e. run through remaining post-async job steps)
            finalize_new_canvas_course(course, request.user.username)
            course_url = settings.CANVAS_SITE_SETTINGS['base_url'] + 'courses/%s' % course['id']
            return redirect(course_url)


class CanvasCourseSiteStatusView(LoginRequiredMixin, TemplateView):
    """ Displays status of async job for template copy """
    template_name = "canvas_course_site_wizard/status.html"