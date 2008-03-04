from StringIO import StringIO
from sqlalchemy import *
from django_sqlalchemy.models import *
from django.core.management.base import AppCommand, CommandError
from django.conf import settings

class Command(AppCommand):
    def handle_app(self, app, **options):
        setup_all()
        
        buf = StringIO()
        engine = create_engine(settings.DJANGO_SQLALCHEMY_DBURI, strategy='mock', executor=lambda s, p='': buf.write(s + p))
        create_all(engine)
        print buf.getvalue()
