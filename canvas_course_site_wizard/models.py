from icommons_common.models import CourseInstance, CourseSite, SiteMap
from django.conf import settings


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
        SiteMap.objects.create(course_instance=self, course_site=site)
        return site

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
