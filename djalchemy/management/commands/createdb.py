from optparse import make_option
from django.core.management.base import NoArgsCommand
from djalchemy.backend.base import metadata


class Command(NoArgsCommand):
    option_list = NoArgsCommand.option_list + (
        make_option(
            '--verbosity', action='store', dest='verbosity', default='1',
            type='choice', choices=['0', '1', '2'],
            help='Verbosity level; 0=minimal output, 1=normal output, 2=all output'),
        make_option(
            '--noinput', action='store_false', dest='interactive',
            default=True,
            help='Tells Django to NOT prompt the user for input of any kind.'),
    )
    help = "Create the database tables for all apps in INSTALLED_APPS whose tables haven't already been created."

    def handle_noargs(self, **options):
        metadata.create_all()
