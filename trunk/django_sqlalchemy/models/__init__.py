try:
    set
except NameError:
    from sets import Set as set

import sqlalchemy
from sqlalchemy.types import *

from django_sqlalchemy.models.options import using_options, using_table_options, \
                           using_mapper_options, options_defaults
from django_sqlalchemy.models.base import Model, ModelBase, EntityDescriptor, \
                          setup_entities, cleanup_entities
from django_sqlalchemy.models.fields import *
# from django_sqlalchemy.models.fields.related import belongs_to, has_one, has_many, \
#                                  has_and_belongs_to_many, \
#                                  ForeignKey, OneToOneField, OneToManyField, ManyToManyField
from django_sqlalchemy.models.properties import has_property, GenericProperty, ColumnProperty
from django_sqlalchemy.models.statements import Statement


__version__ = '0.1.0'

__all__ = ['Field', 'AutoField', 'CharField', 'PhoneNumberField',
           'has_property', 'GenericProperty', 'ColumnProperty',
           'using_options', 'using_table_options', 'using_mapper_options',
           'options_defaults', 'metadata', 'objectstore', 'session',
           'create_all', 'drop_all',
           'setup_all', 'cleanup_all', 
           'setup_entities', 'cleanup_entities'] + \
           sqlalchemy.types.__all__

__doc_all__ = ['create_all', 'drop_all',
               'setup_all', 'cleanup_all',
               'metadata', 'session']


class Objectstore(object):
    """a wrapper for a SQLAlchemy session-making object, such as 
    SessionContext or ScopedSession.
    
    Uses the ``registry`` attribute present on both objects
    (versions 0.3 and 0.4) in order to return the current
    contextual session.
    """
    
    def __init__(self, ctx):
        self.context = ctx

    def __getattr__(self, name):
        return getattr(self.context.registry(), name)
    
    session = property(lambda s:s.context.registry())

# default session
try: 
    from sqlalchemy.orm import scoped_session
    session = scoped_session(sqlalchemy.orm.create_session)
except ImportError: 
    # Not on version 0.4 of sqlalchemy
    from sqlalchemy.ext.sessioncontext import SessionContext
    session = Objectstore(SessionContext(sqlalchemy.orm.create_session))

# backward-compatible name
objectstore = session

# default metadata
metadata = sqlalchemy.MetaData()

metadatas = set()

# default entity collection
entities = list()


def create_all(*args, **kwargs):
    '''Create the necessary tables for all declared entities'''
    for md in metadatas:
        md.create_all(*args, **kwargs)


def drop_all(*args, **kwargs):
    '''Drop tables for all declared entities'''
    for md in metadatas:
        md.drop_all(*args, **kwargs)


def setup_all(create_tables=False, *args, **kwargs):
    '''Setup the table and mapper of all entities in the default entity
    collection.

    This is called automatically if any entity of the collection is configured
    with the `autosetup` option and it is first accessed,
    instanciated (called) or the create_all method of a metadata containing
    tables from any of those entities is called.
    '''
    setup_entities(entities)

    # issue the "CREATE" SQL statements
    if create_tables:
        create_all(*args, **kwargs)


def cleanup_all(drop_tables=False, *args, **kwargs):
    '''Clear all mappers, clear the session, and clear all metadatas. 
    Optionally drops the tables.
    '''
    if drop_tables:
        drop_all(*args, **kwargs)

    cleanup_entities(entities)

    for md in metadatas:
        md.clear()
    metadatas.clear()

    session.clear()

    sqlalchemy.orm.clear_mappers()
    del entities[:]

def create_sql():
    from StringIO import StringIO
    
    buf = StringIO()
    engine = create_engine('postgres://', strategy='mock', executor=lambda s, p='': buf.write(s + p))
    create_all(engine)
    print buf.getvalue()
