
from django.core.management.base import AppCommand

class Command(AppCommand):
    def handle_app(self, app, **options):
        print "hello world %s" % app
