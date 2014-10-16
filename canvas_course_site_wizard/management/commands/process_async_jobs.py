from django.core.management.base import NoArgsCommand
from canvas_course_site_wizard.models import CanvasContentMigrationJob

class Command(NoArgsCommand):
    """
    Process the Content Migration jobs in the CanvasContentMigrationJob table
    """
    help = "Print a help message"

    def handle_noargs(self, **options):
        
        jobs = CanvasContentMigrationJob.objects.filter(workflow_state='queued')
        if jobs.count() == 0:
            # there are no jobs, just exit
            return None

        for job in jobs:
            print job
            # TODO - Check the job url to see if it's complete
            #        if not move on to the next one. If it is
            #        mark it as complete and email the user.
            #        if an error has occured mark it as Failed.
