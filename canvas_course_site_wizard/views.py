from .controller import (create_canvas_course, start_course_template_copy,
                         finalize_new_canvas_course, get_canvas_course_url)
from .mixins import CourseSiteCreationAllowedMixin
from .exceptions import NoTemplateExistsForSchool
from .models import CanvasContentMigrationJob
from braces.views import LoginRequiredMixin
from django.views.generic.base import TemplateView
from django.views.generic.detail import DetailView
from django.template import loader, Context
from django.shortcuts import redirect
from django.http import HttpResponse, HttpResponseServerError
import logging

logger = logging.getLogger(__name__)


class CanvasCourseSiteCreateView(LoginRequiredMixin, CourseSiteCreationAllowedMixin, TemplateView):
    """
    Serves up the canvas course site creation wizard on GET and creates the
    course site on POST.
    """
    template_name = "canvas_course_site_wizard/canvas_wizard.html"

    def post(self, request, *args, **kwargs):

        raise Exception

        sis_course_id = self.object.pk
        sis_user_id = 'sis_user_id:%s' % request.user.username
        course = create_canvas_course(sis_course_id)
        try:
            migration_job = start_course_template_copy(self.object, course['id'], request.user.username)
            return redirect('ccsw-status', migration_job.pk)
        except NoTemplateExistsForSchool:
            # If there is no template to copy, immediately finalize the new course
            # (i.e. run through remaining post-async job steps)
            course_url = finalize_new_canvas_course(course['id'], sis_course_id, sis_user_id)
            return redirect(course_url)
        except Exception as e:
            # This is either a re-raised error or an unknown / unanticipated error; if it is the latter
            # we need to provide some context in our logs to debug the error later
            logger.exception(e)
            raise


class CanvasCourseSiteStatusView(LoginRequiredMixin, DetailView):
    """ Displays status of async job for template copy """
    template_name = "canvas_course_site_wizard/status.html"
    model = CanvasContentMigrationJob
    context_object_name = 'content_migration_job'

    def get_context_data(self, **kwargs):
        """
        get_context_data allows us to pass additional values to the view.
        In this case I am passing in the canvas course url created by the calling
        get_canvas_course_url. 
        """    
        context = super(CanvasCourseSiteStatusView, self).get_context_data(**kwargs)
        logger.debug('Rendering status page for migration job %s' % self.object)
        context['canvas_course_url'] = get_canvas_course_url(canvas_course_id=self.object.canvas_course_id)
        return context


def error_view(request):
    """ test view for showing the customizable error page """

    logger.debug('request.path:%s' % request.path)
    t = loader.get_template('canvas_course_site_wizard/500.html')
    # response = t.render(Context({'app_errors': [{'message': 'Something here'}]}))
    # response = t.render(Context({'app_errors': [{'message': 'Something here'}, {'message': 'second error'}]}))
    response = t.render(Context({'suppress_contact_list': 'true',
                                 'app_errors': [{'message': 'Something here'}, {'message': 'second error'}]}))
    # response = t.render(Context({'error_message': 'Something here', 'show_contact_list': 'true'}))
    return HttpResponseServerError(response)