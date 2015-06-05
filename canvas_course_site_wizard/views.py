import logging
import json

from django.http import HttpResponse
from django.views.generic.base import TemplateView
from django.views.generic.detail import DetailView
from django.shortcuts import redirect
from django.conf import settings

from .controller import (create_canvas_course, start_course_template_copy,
                         finalize_new_canvas_course, get_canvas_course_url,
                         get_bulk_jobs_for_term, get_term_course_counts,
                         is_bulk_job_in_progress, get_courses_for_bulk_create,
                         setup_bulk_jobs)
from .mixins import (CourseSiteCreationAllowedMixin,
                     BulkCourseSiteCreationAllowedMixin)
from icommons_ui.mixins import CustomErrorPageMixin
from .exceptions import NoTemplateExistsForSchool
from .models import (CanvasCourseGenerationJob,
                     BulkCanvasCourseCreationJob)
from icommons_common.models import Term
from braces.views import LoginRequiredMixin

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

        # we modified create_canvas_course to return two params when it's called as part of
        # the single course creation. This is so we can keep track of the job_id
        # for the newly created job record. There's a probably a better way to handle this
        # but for now, this works
        course, course_job_id = create_canvas_course(sis_course_id, request.user.username)
        try:
            course_generation_job = start_course_template_copy(self.object, course['id'],
                                                               request.user.username, course_job_id=course_job_id)
            return redirect('ccsw-status', course_generation_job.pk)
        except NoTemplateExistsForSchool:
            # If there is no template to copy, immediately finalize the new course
            # (i.e. run through remaining post-async job steps)
            course_url = finalize_new_canvas_course(course['id'], sis_course_id, sis_user_id)
            query = CanvasCourseGenerationJob.objects.filter(
                        sis_course_id=sis_course_id, canvas_course_id=course['id'],
                        created_by_user_id=request.user.username)
            job = query.order_by('-created_at')[0]
            job.update_workflow_state(CanvasCourseGenerationJob.STATUS_FINALIZED)
            return redirect(course_url)


class CanvasCourseSiteStatusView(LoginRequiredMixin, DetailView):
    """ Displays status of course creation job, including progress and result of template copy and finalization """
    template_name = "canvas_course_site_wizard/status.html"
    model = CanvasCourseGenerationJob
    context_object_name = 'content_migration_job'

    def get_context_data(self, **kwargs):
        """
        get_context_data allows us to pass additional values to the view. In this case we are passing in:
        - the canvas course url for a successfully completed job (or None if it hasn't successfully completed)
        - simplified job progress status indicators for the template to display success/failure messages
        """
        context = super(CanvasCourseSiteStatusView, self).get_context_data(**kwargs)
        logger.debug('Rendering status page for course generation job %s' % self.object)
        context['canvas_course_url'] = get_canvas_course_url(canvas_course_id=self.object.canvas_course_id)
        context['job_failed'] = self.object.workflow_state in [
            CanvasCourseGenerationJob.STATUS_FAILED,
            CanvasCourseGenerationJob.STATUS_SETUP_FAILED,
            CanvasCourseGenerationJob.STATUS_FINALIZE_FAILED
        ]
        context['job_succeeded'] = self.object.workflow_state in [CanvasCourseGenerationJob.STATUS_FINALIZED]
        return context


class CanvasBulkCreateStatusView(LoginRequiredMixin, BulkCourseSiteCreationAllowedMixin, DetailView):
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

    def post(self, request, *args, **kwargs):
        """
        Process bulk create jobs kicked off by the user for therm term and school specififed.
        """
        sis_term_id = self.request.POST.get('term_id')
        school_id = self.request.POST.get('school_id')

        # if no sis_term_id was supplied in the post request, return and let the user know
        if not sis_term_id:
            return HttpResponse(json.dumps({'error': 'no term_id provided', }),
                                    content_type="application/json", status=500)

        # if no school id was supplied in the post request, return and let the user know
        if not school_id:
            return HttpResponse(json.dumps({'error': 'no school_id provided', }),
                                    content_type="application/json", status=500)

        # if a bulk job is already in progress return and let the user know
        if is_bulk_job_in_progress(sis_term_id):
            return HttpResponse(json.dumps({'success': 'bulk job already in progress for term %s' % sis_term_id, }),
                                content_type="application/json")

        courses = get_courses_for_bulk_create(sis_term_id)
        job = None

        # if there are no courses in the term do not create a bulk job
        if courses.count() > 0:
            logger.info('Creating bulk job')
            job = BulkCanvasCourseCreationJob.objects.create(
                school_id=school_id,
                sis_term_id=sis_term_id,
                status=BulkCanvasCourseCreationJob.STATUS_SETUP,
                created_by_user_id=request.user.username
            )
        else:
            logger.info('User %s tried to bulk create courses for school %s with term %s but there were 0 courses available!' % (request.user.username, school_id, sis_term_id) )
            return HttpResponse(json.dumps({'success': 'no courses are available to create for term %s' % sis_term_id}),
                                    content_type="application/json", status=500)

        errors = setup_bulk_jobs(courses, request.user.username, job.pk)
        messages = dict()
        if errors:
            messages['errors'] = errors

        json_data = json.dumps(messages)
        return HttpResponse(json_data, content_type="application/json")

