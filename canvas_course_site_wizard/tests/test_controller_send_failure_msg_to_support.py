from unittest import TestCase
from mock import patch, DEFAULT, ANY
from django.core import mail
from canvas_course_site_wizard.controller import send_failure_msg_to_support
from django.test.utils import override_settings

import logging
import unittest

# Get an instance of a logger
logger = logging.getLogger(__name__)

@patch.multiple('canvas_course_site_wizard.controller', send_mail = DEFAULT)


class SendMailHelperTest(TestCase):
    longMessage = True

    def setUp(self):
        self.sis_course_id = "12345"
        self.user = "999"
        self.error_detail =" There was a problem in creating the course"
        self.initiator_email = 'sender@test.com'
        self.subject = "Test subject"
        self.message = "Test message"
        self.to_address = ['test@test.com']
        self.from_address = 'sender@test.com'

    @override_settings(CANVAS_EMAIL_NOTIFICATION= {'support_email_body_on_failure':'xyz','support_email_subject_on_failure':'abc','support_email_address':'a','course_migration_failure_subject':'b','course_migration_failure_body':'c' ,'from_email_address': 'd'})
    def test_send_failure_msg_to_support_invoked_with_correct_args(self, send_mail):
        """
        Test that send_mail is called with expected args passed into send_failure_msg_to_support
        """
    	from_address = self.from_address
        result = send_failure_msg_to_support(self.sis_course_id, self.user, self.error_detail)
        send_mail.assertCalledWith(self.subject, self.message, from_address, self.to_address ,fail_silently=ANY)

    @override_settings(CANVAS_EMAIL_NOTIFICATION= {'support_email_body_on_failure':'xyz','support_email_subject_on_failure':'abc','support_email_address':'a','course_migration_failure_subject':'b','course_migration_failure_body':'c' ,'from_email_address': 'd'})
    def test_handling_of_send_mail_exception(self, send_mail):
        """ Test to assert that an exception is raised by send_failure_msg_to_support, when the send_mail throws an exception"""
        from_address = self.from_address
        send_failure_msg_to_support(self.sis_course_id, self.user, self.error_detail)
        send_mail.side_effect = Exception	
        self.assertRaises( Exception, send_failure_msg_to_support, self.sis_course_id, self.user, self.error_detail)
   