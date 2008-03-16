from django.db import models
# class Model(object):
#     __metaclass__ = ClassReplacer(models.Model)
#     
#     def save(self):
#         raise NotImplemented()
#     
#     def delete(self):
#         raise NotImplemented()


try:
    set
except NameError:
    from sets import Set as set

import sys
import warnings

import sqlalchemy
from sqlalchemy                    import Table, Column, Integer, \
                                          desc, ForeignKey, and_
from sqlalchemy.orm                import Query, MapperExtension,\
                                          mapper, object_session, EXT_PASS
from sqlalchemy.ext.sessioncontext import SessionContext

import django_sqlalchemy.models
from django_sqlalchemy.models.statements import process_mutators
from django_sqlalchemy.models import options
from django_sqlalchemy.models.properties import has_property, Property, GenericProperty, ColumnProperty


__doc_all__ = ['Model', 'ModelBase']


try: 
    from sqlalchemy.orm import ScopedSession
except ImportError: 
    # Not on sqlalchemy version 0.4
    ScopedSession = type(None)


def _do_mapping(session, cls, *args, **kwargs):
    if session is None:
        return mapper(cls, *args, **kwargs)
    elif isinstance(session, ScopedSession):
        return session.mapper(cls, *args, **kwargs)
    elif isinstance(session, SessionContext):
        extension = kwargs.pop('extension', None)
        if extension is not None:
            if not isinstance(extension, list):
                extension = [extension]
            extension.append(session.mapper_extension)
        else:
            extension = session.mapper_extension

        class query(object):
            def __getattr__(s, key):
                return getattr(session.registry().query(cls), key)

            def __call__(s):
                return session.registry().query(cls)

        if not 'query' in cls.__dict__: 
            cls.query = query()

        return mapper(cls, extension=extension, *args, **kwargs)
    else:
        raise Exception("Failed to map entity '%s' with its table or "
                        "selectable" % cls.__name__)

class EntityDescriptor(object):
    '''
    EntityDescriptor describes fields and options needed for table creation.
    '''
    
    def __init__(self, entity):
        entity.table = None
        entity.mapper = None

        self.entity = entity
        self.module = sys.modules[entity.__module__]

        self.has_pk = False
        self._pk_col_done = False

        self.builders = []

        self.is_base = is_base(entity)
        self.parent = None
        self.children = []

        for base in entity.__bases__:
            if isinstance(base, ModelBase) and not is_base(base):
                if self.parent:
                    raise Exception('%s entity inherits from several entities,'
                                    ' and this is not supported.' 
                                    % self.entity.__name__)
                else:
                    self.parent = base
                    self.parent._descriptor.children.append(entity)

        # columns and constraints waiting for a table to exist
        self._columns = list()
        self.constraints = list()
        # properties waiting for a mapper to exist
        self.properties = dict()

        #
        self.relationships = list()

        # set default value for options
        self.order_by = None
        self.table_args = list()

        # set default value for options with an optional module-level default
        self.metadata = getattr(self.module, '__metadata__', django_sqlalchemy.models.metadata)
        self.session = getattr(self.module, '__session__', django_sqlalchemy.models.session)
        self.objectstore = None
        self.collection = getattr(self.module, '__entity_collection__',
                                  django_sqlalchemy.models.entities)

        for option in ('autosetup', 'inheritance', 'polymorphic',
                       'autoload', 'tablename', 'shortnames', 
                       'auto_primarykey', 'version_id_col', 
                       'allowcoloverride'):
            setattr(self, option, options.options_defaults[option])

        for option_dict in ('mapper_options', 'table_options'):
            setattr(self, option_dict, 
                    options.options_defaults[option_dict].copy())

    def setup_options(self):
        '''
        Setup any values that might depend on using_options. For example, the 
        tablename or the metadata.
        '''
        django_sqlalchemy.models.metadatas.add(self.metadata)
        if self.collection is not None:
            self.collection.append(self.entity)

        objectstore = None
        session = self.session
        if session is None or isinstance(session, ScopedSession):
            # no stinking objectstore
            pass
        elif isinstance(session, SessionContext):
            objectstore = django_sqlalchemy.models.Objectstore(session)
        elif not hasattr(session, 'registry'):
            # Both SessionContext and ScopedSession have a registry attribute,
            # but objectstores (whether Elixir's or Activemapper's) don't, so 
            # if we are here, it means an Objectstore is used for the session.
#XXX: still true for activemapper post 0.4?            
            objectstore = session
            session = objectstore.context

        self.session = session
        self.objectstore = objectstore

        entity = self.entity
        if self.inheritance == 'concrete' and self.polymorphic:
            raise NotImplementedError("Polymorphic concrete inheritance is "
                                      "not yet implemented.")

        if self.parent:
            if self.inheritance == 'single':
                self.tablename = self.parent._descriptor.tablename

        if entity._meta.db_table:
            self.tablename = entity._meta.db_table
        
        if not self.tablename:
            if self.shortnames:
                self.tablename = entity.__name__.lower()
            else:
                modulename = entity.__module__.replace('.', '_')
                tablename = "%s_%s" % (modulename, entity.__name__)
                self.tablename = tablename.lower()
        elif callable(self.tablename):
            self.tablename = self.tablename(entity)

    #---------------------
    # setup phase methods

    def setup_autoload_table(self):
        self.setup_table(True)

    def create_pk_cols(self):
        """
        Create primary_key columns. That is, call the 'create_pk_cols' 
        builders then add a primary key to the table if it hasn't already got 
        one and needs one. 
        
        This method is "semi-recursive" in some cases: it calls the 
        create_keys method on ForeignKey relationships and those in turn call
        create_pk_cols on their target. It shouldn't be possible to have an 
        infinite loop since a loop of primary_keys is not a valid situation.
        """
        if self._pk_col_done:
            return

        self.call_builders('create_pk_cols')

        if not self.autoload:
            if self.parent:
                if self.inheritance == 'multi':
                    # add columns with foreign keys to the parent's primary 
                    # key columns 
                    parent_desc = self.parent._descriptor
                    for pk_col in parent_desc.primary_keys:
                        colname = "%s_%s" % (self.parent.__name__.lower(),
                                             pk_col.key)

                        # it seems like SA ForeignKey is not happy being given
                        # a real column object when said column is not yet 
                        # attached to a table
                        pk_col_name = "%s.%s" % (parent_desc.tablename, 
                                                 pk_col.key)
                        col = Column(colname, pk_col.type, 
                                     ForeignKey(pk_col_name), primary_key=True)
                        self.add_column(col)
            elif not self.has_pk and self.auto_primarykey:
                if isinstance(self.auto_primarykey, basestring):
                    colname = self.auto_primarykey
                else:
                    colname = options.DEFAULT_AUTO_PRIMARYKEY_NAME
                
                self.add_column(
                    Column(colname, options.DEFAULT_AUTO_PRIMARYKEY_TYPE, 
                           primary_key=True))
        self._pk_col_done = True

    def setup_relkeys(self):
        self.call_builders('create_non_pk_cols')

    def before_table(self):
        self.call_builders('before_table')
        
    def setup_table(self, only_autoloaded=False):
        '''
        Create a SQLAlchemy table-object with all columns that have been 
        defined up to this point.
        '''
        if self.entity.table:
            return

        if self.autoload != only_autoloaded:
            return
        
        if self.parent:
            if self.inheritance == 'single':
                # we know the parent is setup before the child
                self.entity.table = self.parent.table 

                # re-add the entity columns to the parent entity so that they
                # are added to the parent's table (whether the parent's table
                # is already setup or not).
                for col in self.columns:
                    self.parent._descriptor.add_column(col)
                for constraint in self.constraints:
                    self.parent._descriptor.add_constraint(constraint)
                return
            elif self.inheritance == 'concrete': 
                #TODO: we should also copy columns from the parent table if the
                # parent is a base entity (whatever the inheritance type -> elif
                # will need to be changed)
                # copy all columns from parent table
                for col in self.parent._descriptor.columns:
                    self.add_column(col.copy())
                #FIXME: copy constraints. But those are not as simple to copy
                #since the source column must be changed

        if self.polymorphic and self.inheritance in ('single', 'multi') and \
           self.children and not self.parent:
            if not isinstance(self.polymorphic, basestring):
                self.polymorphic = options.DEFAULT_POLYMORPHIC_COL_NAME
                
            self.add_column(Column(self.polymorphic, 
                                   options.POLYMORPHIC_COL_TYPE))

        if self.version_id_col:
            if not isinstance(self.version_id_col, basestring):
                self.version_id_col = options.DEFAULT_VERSION_ID_COL_NAME
            self.add_column(Column(self.version_id_col, Integer))

        # create list of columns and constraints
        if self.autoload:
            args = self.table_args
        else:
            args = self.columns + self.constraints + self.table_args
        
        # specify options
        kwargs = self.table_options

        if self.autoload:
            kwargs['autoload'] = True

        self.entity.table = Table(self.tablename, self.metadata, 
                                  *args, **kwargs)

    def setup_reltables(self):
        self.call_builders('create_tables')

    def after_table(self):
        self.call_builders('after_table')

    def setup_events(self):
        def make_proxy_method(methods):
            def proxy_method(self, mapper, connection, instance):
                for func in methods:
                    ret = func(instance)
                    # I couldn't commit myself to force people to 
                    # systematicaly return EXT_PASS in all their event methods.
                    # But not doing that diverge to how SQLAlchemy works.
                    # I should try to convince Mike to do EXT_PASS by default,
                    # and stop processing as the special case.
#                    if ret != EXT_PASS:
                    if ret is not None and ret != EXT_PASS:
                        return ret
                return EXT_PASS
            return proxy_method

        # create a list of callbacks for each event
        methods = {}
        for name, method in self.entity.__dict__.items():
            if hasattr(method, '_django_sqlalchemy_events'):
                for event in method._django_sqlalchemy_events:
                    event_methods = methods.setdefault(event, [])
                    event_methods.append(method)
        if not methods:
            return
        
        # transform that list into methods themselves
        for event in methods:
            methods[event] = make_proxy_method(methods[event])
        
        # create a custom mapper extension class, tailored to our entity
        ext = type('EventMapperExtension', (MapperExtension,), methods)()
        
        # then, make sure that the entity's mapper has our mapper extension
        self.add_mapper_extension(ext)

    def before_mapper(self):
        self.call_builders('before_mapper')

    def _get_children(self):
        children = self.children[:]
        for child in self.children:
            children.extend(child._descriptor._get_children())
        return children

    def translate_order_by(self, order_by):
        if isinstance(order_by, basestring):
            order_by = [order_by]
        
        order = list()
        for colname in order_by:
            col = self.get_column(colname.strip('-'))
            if colname.startswith('-'):
                col = desc(col)
            order.append(col)
        return order

    def setup_mapper(self):
        '''
        Initializes and assign an (empty!) mapper to the entity.
        '''
        if self.entity.mapper:
            return
        
        kwargs = self.mapper_options
        if self.order_by:
            kwargs['order_by'] = self.translate_order_by(self.order_by)
        
        if self.version_id_col:
            kwargs['version_id_col'] = self.get_column(self.version_id_col)

        if self.inheritance in ('single', 'concrete', 'multi'):
            if self.parent and \
               not (self.inheritance == 'concrete' and not self.polymorphic):
                kwargs['inherits'] = self.parent.mapper

            if self.inheritance == 'multi' and self.parent:
                col_pairs = zip(self.primary_keys,
                                self.parent._descriptor.primary_keys)
                kwargs['inherit_condition'] = \
                    and_(*[pc == c for c,pc in col_pairs])

            if self.polymorphic:
                if self.children and not self.parent:
                    kwargs['polymorphic_on'] = \
                        self.get_column(self.polymorphic)
                    #TODO: this is an optimization, and it breaks the multi
                    # table polymorphic inheritance test with a relation. 
                    # So I turn it off for now. We might want to provide an 
                    # option to turn it on.
#                    if self.inheritance == 'multi':
#                        children = self._get_children()
#                        join = self.entity.table
#                        for child in children:
#                            join = join.outerjoin(child.table)
#                        kwargs['select_table'] = join
                    
                if self.children or self.parent:
                    #TODO: make this customizable (both callable and string)
                    #TODO: include module name
                    kwargs['polymorphic_identity'] = \
                        self.entity.__name__.lower()

                if self.inheritance == 'concrete':
                    kwargs['concrete'] = True

        if 'primary_key' in kwargs:
            cols = self.entity.table.c
            kwargs['primary_key'] = [getattr(cols, colname) for
                colname in kwargs['primary_key']]

        if self.parent and self.inheritance == 'single':
            args = []
        else:
            args = [self.entity.table]

        self.entity.mapper = _do_mapping(self.session, self.entity,
                                         properties=self.properties,
                                         *args, **kwargs)

    def after_mapper(self):
        self.call_builders('after_mapper')

    def setup_properties(self):
        self.call_builders('create_properties')

    def finalize(self):
        self.call_builders('finalize')
        self.entity._setup_done = True

    #----------------
    # helper methods

    def call_builders(self, what):
        for builder in self.builders:
            if hasattr(builder, what):
                getattr(builder, what)()

    def add_column(self, col, check_duplicate=None):
        '''when check_duplicate is None, the value of the allowcoloverride
        option of the entity is used.
        '''
        if check_duplicate is None:
            check_duplicate = not self.allowcoloverride
        
        if check_duplicate and self.get_column(col.key, False) is not None:
            raise Exception("Column '%s' already exist in '%s' ! " % 
                            (col.key, self.entity.__name__))
        self._columns.append(col)
        
        if col.primary_key:
            self.has_pk = True

        # Autosetup triggers shouldn't be active anymore at this point, so we
        # can theoretically access the entity's table safely. But the problem 
        # is that if, for some reason, the "trigger" removal phase didn't 
        # happen, we'll get an infinite loop. So we just make sure we don't 
        # get one in any case.
        table = type.__getattribute__(self.entity, 'table')
        if table:
            if check_duplicate and col.key in table.columns.keys():
                raise Exception("Column '%s' already exist in table '%s' ! " % 
                                (col.key, table.name))
            table.append_column(col)

    def add_constraint(self, constraint):
        self.constraints.append(constraint)
        
        table = self.entity.table
        if table:
            table.append_constraint(constraint)

    def add_property(self, name, property, check_duplicate=True):
        if check_duplicate and name in self.properties:
            raise Exception("property '%s' already exist in '%s' ! " % 
                            (name, self.entity.__name__))
        self.properties[name] = property
        mapper = self.entity.mapper
        if mapper:
            mapper.add_property(name, property)
        
    def add_mapper_extension(self, extension):
        extensions = self.mapper_options.get('extension', [])
        if not isinstance(extensions, list):
            extensions = [extensions]
        extensions.append(extension)
        self.mapper_options['extension'] = extensions

    def get_column(self, key, check_missing=True):
        "need to support both the case where the table is already setup or not"
        #TODO: support SA table/autoloaded entity
        for col in self.columns:
            if col.key == key:
                return col
        if check_missing:
            raise Exception("No column named '%s' found in the table of the "
                            "'%s' entity!" % (key, self.entity.__name__))
        return None

    def get_inverse_relation(self, rel, reverse=False):
        '''
        Return the inverse relation of rel, if any, None otherwise.
        '''

        matching_rel = None
        for other_rel in self.relationships:
            if other_rel.is_inverse(rel):
                if matching_rel is None:
                    matching_rel = other_rel
                else:
                    raise Exception(
                            "Several relations match as inverse of the '%s' "
                            "relation in entity '%s'. You should specify "
                            "inverse relations manually by using the inverse "
                            "keyword."
                            % (rel.name, rel.entity.__name__))
        # When a matching inverse is found, we check that it has only
        # one relation matching as its own inverse. We don't need the result
        # of the method though. But we do need to be careful not to start an
        # infinite recursive loop.
        if matching_rel and not reverse:
            rel.entity._descriptor.get_inverse_relation(matching_rel, True)

        return matching_rel

    def find_relationship(self, name):
        for rel in self.relationships:
            if rel.name == name:
                return rel
        if self.parent:
            return self.parent.find_relationship(name)
        else:
            return None

    def columns(self):
        #FIXME: this would be more correct but it breaks inheritance, so I'll 
        # use the old test for now.
#        if self.entity.table:
        if self.autoload: 
            return self.entity.table.columns
        else:
            #FIXME: depending on the type of inheritance, we should also 
            # return the parent entity's columns (for example for order_by 
            # using a column defined in the parent.
            return self._columns
    columns = property(columns)

    def primary_keys(self):
        if self.autoload:
            return [col for col in self.entity.table.primary_key.columns]
        else:
            if self.parent and self.inheritance == 'single':
                return self.parent._descriptor.primary_keys
            else:
                return [col for col in self.columns if col.primary_key]
    primary_keys = property(primary_keys)


class TriggerProxy(object):
    """A class that serves as a "trigger" ; accessing its attributes runs
    the setup_all function.

    Note that the `setup_all` is called on each access of the attribute.
    """

    def __init__(self, class_, attrname):
        self.class_ = class_
        self.attrname = attrname

    def __getattr__(self, name):
        django_sqlalchemy.models.setup_all()
        #FIXME: it's possible to get an infinite loop here if setup_all doesn't
        #remove the triggers for this entity. This can happen if the entity is
        #not in the `entities` list for some reason.
        proxied_attr = getattr(self.class_, self.attrname)
        return getattr(proxied_attr, name)

    def __repr__(self):
        proxied_attr = getattr(self.class_, self.attrname)
        return "<TriggerProxy (%s)>" % (self.class_.__name__)


class TriggerAttribute(object):

    def __init__(self, attrname):
        self.attrname = attrname

    def __get__(self, instance, owner):
        #FIXME: it's possible to get an infinite loop here if setup_all doesn't
        #remove the triggers for this entity. This can happen if the entity is
        #not in the `entities` list for some reason.
        django_sqlalchemy.models.setup_all()
        return getattr(owner, self.attrname)

def is_base(cls):
    """
    Scan bases classes to see if any is an instance of ModelBase. If we
    don't find any, it means the current entity is a base class (like 
    the 'Model' class).
    """
    for base in cls.__bases__:
        if isinstance(base, ModelBase):
            return False
    return True

class ModelBase(models.base.ModelBase):
    """
    Model base meta class. 
    You should only use it directly if you want to define your own base class 
    for your entities (ie you don't want to use the provided 'Model' class).
    """
    _entities = {}
    
    def __new__(cls, name, bases, attrs):
        try:
            parents = [b for b in bases if issubclass(b, Model)]
            if not parents:
                return type.__new__(cls, name, bases, attrs)
        except NameError:
            # 'Model' isn't defined yet, meaning we're looking at Django's own
            # Model class, defined below.
            return type.__new__(cls, name, bases, attrs)
        
        return super(ModelBase, cls).__new__(cls, name, bases, attrs)
    
    def __init__(cls, name, bases, dict_):
        # Only process further subclasses of the base classes (Entity et al.),
        # not the base classes themselves. We don't want the base entities to 
        # be registered in an entity collection, nor to have a table name and 
        # so on. 
        if is_base(cls):
            return
        
        # build a dict of entities for each frame where there are entities
        # defined
        caller_frame = sys._getframe(1)
        cid = cls._caller = id(caller_frame)
        caller_entities = ModelBase._entities.setdefault(cid, {})
        caller_entities[name] = cls
        # Append all entities which are currently visible by the entity. This 
        # will find more entities only if some of them where imported from 
        # another module.
        for entity in [e for e in caller_frame.f_locals.values() 
                         if isinstance(e, ModelBase)]:
            caller_entities[entity.__name__] = entity
        
        # create the entity descriptor
        desc = cls._descriptor = EntityDescriptor(cls)
        
        # Process attributes (using the assignment syntax), looking for 
        # 'Property' instances and attaching them to this entity.
        properties = [(name, attr) for name, attr in dict_.iteritems() 
                                   if isinstance(attr, Property)]
        sorted_props = sorted(properties, key=lambda i: i[1]._counter)
        
        for name, prop in sorted_props:
            prop.attach(cls, name)
        
        # sa_options = dict([(m, getattr(dict_['Sa'], m)) for m in dir(dict_['Sa']) if m not in ('__doc__', '__module__')])
        # options.using_options(sa_options)
        
        # Process mutators. Needed before _install_autosetup_triggers so that
        # we know of the metadata
        process_mutators(cls)

        # setup misc options here (like tablename etc.)
        desc.setup_options()

        # create trigger proxies
        # TODO: support entity_name... It makes sense only for autoloaded 
        # tables for now, and would make more sense if we support "external"
        # tables
        if desc.autosetup:
            _install_autosetup_triggers(cls)

    def __call__(cls, *args, **kwargs):
        if cls._descriptor.autosetup and not hasattr(cls, '_setup_done'):
            django_sqlalchemy.models.setup_all()
        return type.__call__(cls, *args, **kwargs)

def _install_autosetup_triggers(cls, entity_name=None):
    #TODO: move as much as possible of those "_private" values to the
    # descriptor, so that we don't mess the initial class.
    tablename = cls._descriptor.tablename
    schema = cls._descriptor.table_options.get('schema', None)
    cls._table_key = sqlalchemy.schema._get_table_key(tablename, schema)

    table_proxy = TriggerProxy(cls, 'table')

    md = cls._descriptor.metadata
    md.tables[cls._table_key] = table_proxy

    # We need to monkeypatch the metadata's table iterator method because 
    # otherwise it doesn't work if the setup is triggered by the 
    # metadata.create_all().
    # This is because ManyToManyField relationships add tables AFTER the list 
    # of tables that are going to be created is "computed" 
    # (metadata.tables.values()).
    # see:
    # - table_iterator method in MetaData class in sqlalchemy/schema.py 
    # - visit_metadata method in sqlalchemy/ansisql.py
    original_table_iterator = md.table_iterator
    if not hasattr(original_table_iterator, 
                   '_non_django_sqlalchemy_patched_iterator'):
        def table_iterator(*args, **kwargs):
            django_sqlalchemy.models.setup_all()
            return original_table_iterator(*args, **kwargs)
        table_iterator.__doc__ = original_table_iterator.__doc__
        table_iterator._non_django_sqlalchemy_patched_iterator = \
            original_table_iterator
        md.table_iterator = table_iterator

    #TODO: we might want to add all columns that will be available as
    #attributes on the class itself (in SA 0.4). This would be a pretty
    #rare usecase, as people will hit the query attribute before the
    #column attributes, but still...
    for name in ('c', 'table', 'mapper', 'query'):
        setattr(cls, name, TriggerAttribute(name))
    
    #TODO: trigger all managers so when they are accessed the class is setup

    cls._has_triggers = True


def _cleanup_autosetup_triggers(cls):
    if not hasattr(cls, '_has_triggers'):
        return

    for name in ('table', 'mapper'):
        setattr(cls, name, None)

    for name in ('c', 'query'):
        delattr(cls, name)

    desc = cls._descriptor
    md = desc.metadata

    # the fake table could have already been removed (namely in a 
    # single table inheritance scenario)
    md.tables.pop(cls._table_key, None)

    # restore original table iterator if not done already
    if hasattr(md.table_iterator, '_non_django_sqlalchemy_patched_iterator'):
        md.table_iterator = \
            md.table_iterator._non_django_sqlalchemy_patched_iterator

    del cls._has_triggers

    
def setup_entities(entities):
    '''Setup all entities in the list passed as argument'''
    for entity in entities:
        if entity._descriptor.autosetup:
            _cleanup_autosetup_triggers(entity)
    for method_name in (
            'setup_autoload_table', 'create_pk_cols', 'setup_relkeys',
            'before_table', 'setup_table', 'setup_reltables', 'after_table',
            'setup_events',
            'before_mapper', 'setup_mapper', 'after_mapper',
            'setup_properties',
            'finalize'):
        for entity in entities:
            if hasattr(entity, '_setup_done'):
                continue
            method = getattr(entity._descriptor, method_name)
            method()


def cleanup_entities(entities):
    """
    Try to revert back the list of entities passed as argument to the state 
    they had just before their setup phase. It will not work entirely for 
    autosetup entities as we need to remove the autosetup triggers.

    As of now, this function is *not* functional in that it doesn't revert to 
    the exact same state the entities were before setup. For example, the 
    properties do not work yet as those would need to be regenerated (since the
    columns they are based on are regenerated too -- and as such the 
    corresponding joins are not correct) but this doesn't happen because of 
    the way relationship setup is designed to be called only once (especially 
    the backref stuff in create_properties).
    """
    for entity in entities:
        desc = entity._descriptor
        if desc.autosetup:
            _cleanup_autosetup_triggers(entity)

        if hasattr(entity, '_setup_done'):
            del entity._setup_done

        entity.table = None
        entity.mapper = None
        
        desc._pk_col_done = False
        desc.has_pk = False
        desc._columns = []
        desc.constraints = []
        desc.properties = {}

class ObjectSessionProxy(object):
    def __init__(self, session, instance):
        self.session = session
        self.instance = instance
        
    def flush(self):
        return self.session.flush([self.instance])
    
    def delete(self):
        return self.session.delete(self.instance)
    
    def expire(self):
        return self.session.expire(self.instance)
    
    def refresh(self):
        return self.session.refresh(self.instance)
    
    def expunge(self):
        return self.session.expunge(self.instance)

class Model(models.Model):
    '''
    The base class for all entities
    
    All Elixir model objects should inherit from this class. Statements can
    appear within the body of the definition of an entity to define its
    fields, relationships, and other options.
    
    Here is an example:

    .. sourcecode:: python
    
        class Person(Entity):
            name = Field(Unicode(128))
            birthdate = Field(DateTime, default=datetime.now)
    
    Please note, that if you don't specify any primary keys, Elixir will
    automatically create one called ``id``.
    
    For further information, please refer to the provided examples or
    tutorial.
    '''
    __metaclass__ = ModelBase
    
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
        return super(Model, self).__init__(**kwargs)
    
    def set(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def _get_session(self):
        return ObjectSessionProxy(object_session(self), self)
    session = property(_get_session)

    # This bunch of session methods, along with all the query methods below 
    # only make sense when using a global/scoped/contextual session.
    def _global_session(self):
        return self._descriptor.session.registry()
    _global_session = property(_global_session)

    def merge(self, *args, **kwargs):
        return self._global_session.merge(self, *args, **kwargs)

    def save(self, *args, **kwargs):
        # Here we force a flush which will commit the transaction. this will
        # be bad once we need to support transactions with django.
        obj = self._global_session.save(self, *args, **kwargs)
        self.session.flush()
        return obj

    def update(self, *args, **kwargs):
        return self._global_session.update(self, *args, **kwargs)

    def save_or_update(self, *args, **kwargs):
        return self._global_session.save_or_update(self, *args, **kwargs)

    # query methods
    # def get_by(cls, *args, **kwargs):
    #     return cls.query.filter_by(*args, **kwargs).first()
    # get_by = classmethod(get_by)
    # 
    # def get(cls, *args, **kwargs):
    #     return cls.query.get(*args, **kwargs)
    # get = classmethod(get)
