from icommons_common.models import CourseInstance
from django.db import models


class SISCourseDataMixin(object):
    """
    Extends an SIS-fed CourseInstance object with methods and properties needed for course site
    creation in an extenal LMS.  Designed as a mixin to make unit testing easier.
    """
    @property
    def sis_account_id(self):
        """
        Derives an sis_account_id for this course.  Repeated calls will return the previously
        calculated value.
        :returns: formatted string
        """
        if not hasattr(self, '_sis_account_id'):
            if self.course.course_groups.count() > 0:
                self._sis_account_id = 'coursegroup:%d' % self.course.course_groups.first().pk
            elif self.course.departments.count() > 0:
                self._sis_account_id = 'dept:%d' % self.course.departments.first().pk
            else:
                self._sis_account_id = 'school:%s' % self.course.school_id
        return self._sis_account_id

    @property
    def course_code(self):
        """
        Derives the course code for this course.  Repeated calls will return the previously
        calculated value.
        :returns: string
        """
        if not hasattr(self, '_course_code'):
            if self.short_title:
                self._course_code = self.short_title
            elif self.course.registrar_code_display:
                self._course_code = self.course.registrar_code_display
            else:
                self._course_code = self.course.registrar_code
        return self._course_code

    @property
    def course_name(self):
        """
        Derives the course name for this course.  Appends the sub_title field to the name if :
        present.
        :returns: formatted string
        """
        if not hasattr(self, '_course_name'):
            cname = self.title or self.course_code
            if self.sub_title:
                cname += ': %s' % self.sub_title
            self._course_name = cname
        return self._course_name

    @property
    def sis_term_id(self):
        """
        Calculates and returns the sis_term_id for this course.  Repeated calls will return the
        previously calculated value.
        :returns: formatted string or None
        """
        if not hasattr(self, '_sis_term_id'):
            self._sis_term_id = self.term.meta_term_id()
        return self._sis_term_id

    @property
    def school_code(self):
        """
        Returns the school code for this course.
        :returns: string
        """
        return self.course.school_id

    def primary_section_name(self):
        """
        Derives the name of the primary (main) section for this course.
        :returns: formatted string
        """
        return '%s %s' % (self.course.school_id.upper(), self.course_code)


class SISCourseData(CourseInstance, SISCourseDataMixin):
    """
    Database-backed SIS course information that implements mixin.
    """
    class Meta:
        proxy = True

class CanvasContentMigrationJob(models.Model):
    # Workflow status values
    STATUS_QUEUED = 'queued'
    STATUS_RUNNING = 'running'
    STATUS_COMPLETED = 'completed'
    STATUS_FAILED = 'failed'
    # Workflow status choices
    WORKFLOW_STATUS_CHOICES = (
        (STATUS_QUEUED, STATUS_QUEUED),
        (STATUS_RUNNING, STATUS_RUNNING),
        (STATUS_COMPLETED, STATUS_COMPLETED),
        (STATUS_FAILED, STATUS_FAILED),
    )
    canvas_course_id = models.IntegerField(max_length=10,db_index=True)
    sis_course_id = models.CharField(max_length=20, db_index=True)
    content_migration_id = models.IntegerField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)
    status_url = models.CharField(max_length=200)
    workflow_state = models.CharField(max_length=20, choices=WORKFLOW_STATUS_CHOICES, default=STATUS_QUEUED)
    created_by_user_id = models.CharField(max_length=20)
    class Meta:
        db_table = u'canvas_content_migration_job'

    def __unicode__(self):
        return self.sis_course_id

