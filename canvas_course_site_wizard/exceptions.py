class NoTemplateExistsForSchool(Exception):
    def __init__(self, school_id):
        self.school_id = school_id

    def __unicode__(self):
        return u'No template exists for school_id=%s' % self.school_id


class NoCanvasUserToEnroll(Exception):
    def __init__(self, user_id):
        self.user_id = user_id

    def __unicode__(self):
        return u'No Canvas user with user_id=%s.' % self.user_id
