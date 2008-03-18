import sqlalchemy
from sqlalchemy import *
from sqlalchemy.types import *
from sqlalchemy.orm import relation, sessionmaker, scoped_session
from django_sqlalchemy.models.fields import *
from django.conf import settings
from django_sqlalchemy.models.base import Model

__all__ = ['Field', 'AutoField', 'CharField', 'PhoneNumberField',
           'metadata', 'session'] + \
           sqlalchemy.types.__all__

__doc_all__ = ['create_all', 'drop_all',
	           'setup_all', 'cleanup_all',
	           'metadata', 'session']

engine = create_engine(settings.DJANGO_SQLALCHEMY_DBURI)
Session = scoped_session(sessionmaker(bind=engine, autoflush=True, transactional=True))
session = Session()

# default metadata
metadata = sqlalchemy.MetaData(bind=engine)

if getattr(settings, 'DJANGO_SQLALCHEMY_ECHO'):
    metadata.bind.echo = settings.DJANGO_SQLALCHEMY_ECHO

# Base = declarative_base(engine, metadata)

