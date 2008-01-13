try:
    set
except NameError:
    from sets import Set as set

from base import Model
from fields import *
import sqlalchemy

# from elixir.options import using_options, using_table_options, \
#                            using_mapper_options, options_defaults
# from elixir.entity import Entity, EntityMeta, EntityDescriptor, \
#                           setup_entities, cleanup_entities
# from elixir.fields import has_field, with_fields, Field
# from elixir.relationships import belongs_to, has_one, has_many, \
#                                  has_and_belongs_to_many, \
#                                  ManyToOne, OneToOne, OneToMany, ManyToMany
# from elixir.properties import has_property, GenericProperty, ColumnProperty
# from elixir.statements import Statement

__version__ = '0.1.0'

__all__ = ['Entity', 'EntityMeta',
           'Field', 'has_field', 'with_fields',
           'has_property', 'GenericProperty', 'ColumnProperty',
           'belongs_to', 'has_one', 'has_many', 'has_and_belongs_to_many',
           'ManyToOne', 'OneToOne', 'OneToMany', 'ManyToMany',
           'using_options', 'using_table_options', 'using_mapper_options',
           'options_defaults', 'metadata', 'session',
           'create_all', 'drop_all',
           'setup_all', 'cleanup_all', 
           'setup_entities', 'cleanup_entities'] 

__doc_all__ = ['create_all', 'drop_all',
               'setup_all', 'cleanup_all',
               'metadata', 'session']

from sqlalchemy.orm import scoped_session
session = scoped_session(sqlalchemy.orm.create_session)

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
