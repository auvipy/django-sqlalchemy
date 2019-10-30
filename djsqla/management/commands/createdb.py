from django.core.management.base import NoArgsCommand
from db.backend.base import metadata


class Command(NoArgsCommand):
    option_list = NoArgsCommand.option_list + (

    )
    help = "Create the database tables for all apps in INSTALLED_APPS whose tables haven't already been created."

    def handle_noargs(self, **options):
        metadata.create_all()
