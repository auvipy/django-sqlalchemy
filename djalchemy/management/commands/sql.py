
from cStringIO import StringIO
from sqlalchemy import create_engine
from django_sqlalchemy.backend.base import metadata
from django.core.management.base import AppCommand, CommandError
from django.conf import settings
from django.db.models.loading import get_models

class Command(AppCommand):
    def handle_app(self, app, **options):
        buf = StringIO()
        def buffer_output(s, p=""):
            return buf.write(s + p)
        engine = create_engine(settings.DJANGO_SQLALCHEMY_DBURI,
            strategy="mock",
            executor=buffer_output)
        metadata.create_all(engine,
            tables=[m.__table__ for m in get_models(app)])
        print buf.getvalue()
