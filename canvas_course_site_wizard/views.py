from .controller import (create_canvas_course, start_course_template_copy,
                         finalize_new_canvas_course, get_canvas_course_url,
                         get_bulk_jobs_for_term, get_term_course_counts,
                         is_bulk_job_in_progress)
from .mixins import CourseSiteCreationAllowedMixin
from icommons_ui.mixins import CustomErrorPageMixin
from .exceptions import NoTemplateExistsForSchool
from .models import CanvasContentMigrationJob
from icommons_common.models import Term
from braces.views import LoginRequiredMixin
from django.views.generic.base import TemplateView
from django.views.generic.detail import DetailView
from django.shortcuts import redirect
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


class CanvasCourseSiteCreateView(LoginRequiredMixin, CourseSiteCreationAllowedMixin, CustomErrorPageMixin, TemplateView):
    """
    Serves up the canvas course site creation wizard on GET and creates the
    course site on POST.
    """
    template_name = "canvas_course_site_wizard/canvas_wizard.html"
    # This is currently the project-level 500 error page, which has RenderableException logic
    custom_error_template_name = "500.html"

    def post(self, request, *args, **kwargs):
        sis_course_id = self.object.pk
        sis_user_id = 'sis_user_id:%s' % request.user.username
        course = create_canvas_course(sis_course_id,request.user.username)
        try:
            migration_job = start_course_template_copy(self.object, course['id'], request.user.username)
            return redirect('ccsw-status', migration_job.pk)
        except NoTemplateExistsForSchool:
            # If there is no template to copy, immediately finalize the new course
            # (i.e. run through remaining post-async job steps)
            course_url = finalize_new_canvas_course(course['id'], sis_course_id, sis_user_id)
            return redirect(course_url)


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


class CanvasBulkCreateStatusView(LoginRequiredMixin, DetailView):
    """
    Displays term info and the bulk create button, also gives the user
    a link back the the term tool term edit page
    """
    template_name = "canvas_course_site_wizard/bulk_create.html"
    model = Term
    context_object_name = 'term'

    def get_context_data(self, **kwargs):
        """
        get_context_data allows us to pass additional values to the view.
        In this case I am passing in total_courses and total_canvas_courses to display in the view.
        """
        context = super(CanvasBulkCreateStatusView, self).get_context_data(**kwargs)
        logger.debug('bulk create job %s' % self.object)
        context.update(get_term_course_counts(self.object.pk))
        context['is_job_in_progress'] = is_bulk_job_in_progress(self.object.pk)
        context['bulk_jobs'] = get_bulk_jobs_for_term(self.object.pk)
        context['ext_tools_term_edit_url'] = '%s/tools/term_tool/term/%s/edit' % (settings.COURSE_WIZARD.get('TERM_TOOL_BASE_URL'), self.object.pk)
        return context
