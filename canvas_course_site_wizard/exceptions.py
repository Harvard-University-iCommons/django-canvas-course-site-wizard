class NoTemplateExistsForSchool(Exception):
    def __init__(self, school_id):
        self.school_id = school_id

    def __unicode__(self):
        return repr(self.school_id)


class NoCanvasUserToEnroll(Exception):
    def __init__(self, sis_user_id, canvas_account_id):
        self.sis_user_id = sis_user_id
        self.canvas_account_id = canvas_account_id

    def __unicode__(self):
        return u'User with sis_user_id=%s does not exist in canvas_account_id=%s' % (self.sis_user_id,
                                                                                     self.canvas_account_id)

class TooManyMatchingUsersToEnroll(Exception):
    def __init__(self, sis_user_id, canvas_account_id):
        self.sis_user_id = sis_user_id
        self.canvas_account_id = canvas_account_id

    def __unicode__(self):
        return u'More than one user matching sis_user_id=%s exist in canvas_account_id=%s' % (self.sis_user_id,
                                                                                              self.canvas_account_id)