from cStringIO import StringIO
from sqlalchemy import create_engine
from django_sqlalchemy.models import metadata
from django.core.management.base import AppCommand, CommandError
from django.conf import settings

class Command(AppCommand):
    def handle_app(self, app, **options):
        buf = StringIO()
        def buffer_output(s, p=""):
            return buf.write(s + p)
        engine = create_engine(settings.DJANGO_SQLALCHEMY_DBURI,
            strategy="mock",
            executor=buffer_output)
        # TODO: make use of the app, see #1.
        metadata.create_all(engine)
        print buf.getvalue()
