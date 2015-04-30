from icommons_common.models import CourseInstance, CourseSite, SiteMap, SiteMapType
from django.conf import settings
from django.db import models


class SISCourseDataMixin(object):
    """
    Extends an SIS-fed CourseInstance object with methods and properties needed for course site
    creation in an extenal LMS.  Designed as a mixin to make unit testing easier.
    """

    # Class constants for the sync_to_canvas column / flag used by set_sync_to_canvas()
    TURN_ON_SYNC_TO_CANVAS = 1
    TURN_OFF_SYNC_TO_CANVAS = 0

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

    def get_official_course_site_url(self):
        """
        Return the url for the official course website associated with this course.  If more than
        one course site is marked as official, returns the url for the first one.
        :return: url or None
        """
        if not hasattr(self, '_official_course_site_url'):
            official_sites = self.sites.filter(sitemap__map_type_id='official')
            if official_sites:
                # We're making the decision at this point to get the first official site provided.
                # If the site_type_id is 'isite' we need to build the url and append the keyword
                # if not, then we have a whole url for the external site so we can use it directly.
                site = official_sites[0]
                if site.site_type_id == 'isite':
                    self._official_course_site_url = getattr(settings, 'ISITES_LMS_URL', 'http://') + site.external_id
                else:
                    self._official_course_site_url = site.external_id
            else:
                self._official_course_site_url = None
        return self._official_course_site_url

    def set_official_course_site_url(self, url):
        """
        Creates the records necessary to make the given url the official course site for this course.
        Returns the newly created CourseSite object.
        """
        site = CourseSite.objects.create(site_type_id='external', external_id=url)
        sitemap_type = SiteMapType.objects.get(map_type_id='official')
        SiteMap.objects.create(course_instance=self, course_site=site, map_type=sitemap_type)
        return site

    def primary_section_name(self):
        """
        Derives the name of the primary (main) section for this course.
        :returns: formatted string
        """
        return '%s %s' % (self.course.school_id.upper(), self.course_code)

    def set_sync_to_canvas(self, sync_to_canvas_flag):
        """
        Updates the sync_to_canvas column of the course instance record. Currently the
        values being used are 0(no sync) and 1 (sync). But  there is some discussion to use more 
        values to to do partial sync(teaching staff only, students only , etc) in the future.
        Returns the updated object  - of type SISCourseDataMixin.
        """
        self.sync_to_canvas = sync_to_canvas_flag
        self.save(update_fields=['sync_to_canvas'])
        return self


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
    canvas_course_id = models.IntegerField(max_length=10, db_index=True)
    sis_course_id = models.CharField(max_length=20, db_index=True)
    content_migration_id = models.IntegerField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)
    status_url = models.CharField(max_length=200)
    workflow_state = models.CharField(max_length=20, choices=WORKFLOW_STATUS_CHOICES, default=STATUS_QUEUED)
    created_by_user_id = models.CharField(max_length=20)
    bulk_job_id = models.IntegerField(max_length=11, null=True, blank=True)

    
    class Meta:
        db_table = u'canvas_content_migration_job'

    def __unicode__(self):
        #TODO: unit test for this method (skipped to support bug fix in QA testing)
        return "(CanvasContentMigrationJob ID=%s: sis_course_id=%s | %s)" % (self.pk, self.sis_course_id,
                                                                              self.workflow_state)


class CanvasSchoolTemplate(models.Model):
    template_id = models.IntegerField(max_length=10)
    school_id = models.CharField(max_length=10, db_index=True)

    class Meta:
        db_table = u'canvas_school_template'

    def __unicode__(self):
        #TODO: unit test for this method (skipped to support bug fix in QA testing)
        return "(CanvasSchoolTemplate ID=%s: school_id=%s | template_id=%s" % (self.pk, self.school_id,
                                                                               self.template_id)

class BulkJob(models.Model):
    # status values
    STATUS_SETUP = 'setup'
    STATUS_PENDING = 'pending'
    STATUS_FINALIZING = 'finalizing'
    STATUS_NOTIFICATION_SUCCESSFUL = 'notification_successful'
    STATUS_NOTIFICATION_FAILED = 'notification_failed'

    # status choices
    STATUS_CHOICES = (
        (STATUS_SETUP, STATUS_SETUP),
        (STATUS_PENDING, STATUS_PENDING),
        (STATUS_FINALIZING, STATUS_FINALIZING),
        (STATUS_NOTIFICATION_SUCCESSFUL, STATUS_NOTIFICATION_SUCCESSFUL),
        (STATUS_NOTIFICATION_FAILED, STATUS_NOTIFICATION_FAILED),
    )
    bulk_job_id = models.IntegerField(max_length=11, db_index=True)
    school_id = models.CharField(max_length=10)
    sis_term_id = models.IntegerField(max_length=11)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default=STATUS_SETUP)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by_user_id = models.CharField(max_length=20)
    updated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = u'bulk_job'

    def __unicode__(self):
        return "(BulkJob ID=%s: sis_term_id=%s | %s)" % (self.pk, self.sis_term_id)
