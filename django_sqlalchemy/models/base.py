from django_sqlalchemy.models import *
from django.db import models
from sqlalchemy import *
from sqlalchemy.schema import Table, SchemaItem, Column, MetaData
from sqlalchemy.orm import synonym as _orm_synonym, mapper, relation, sessionmaker, scoped_session
from sqlalchemy.orm.interfaces import MapperProperty
from sqlalchemy.orm.properties import PropertyLoader

engine = create_engine(settings.DJANGO_SQLALCHEMY_DBURI)
Session = scoped_session(sessionmaker(bind=engine, autoflush=True, transactional=True))
session = Session()

# default metadata
metadata = sqlalchemy.MetaData(bind=engine)

if getattr(settings, 'DJANGO_SQLALCHEMY_ECHO'):
    metadata.bind.echo = settings.DJANGO_SQLALCHEMY_ECHO

__all__ = ['Model', 'declarative_base', 'declared_synonym']

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
    
    def __init__(cls, classname, bases, dict_):
        if '_decl_class_registry' in cls.__dict__:
            return type.__init__(cls, classname, bases, dict_)
        
        cls._decl_class_registry[classname] = cls
        our_stuff = []
        
        if not isinstance(cls._meta.pk, AutoField):
            auto = AutoField(verbose_name='ID', primary_key=True, auto_created=True)
            auto.name = "id"
            our_stuff.append(auto.create_column())
        for field in cls._meta.fields:
            if isinstance(field, Field):
                our_stuff.append(field.create_column())
        
        autoload = cls.__dict__.get('__autoload__')
        if autoload:
            table_kw = {'autoload': True}
        else:
            table_kw = {}
        
        cls.__table__ = table = Table(cls._meta.db_table, cls.metadata, *our_stuff, **table_kw)
        
        inherits = cls.__mro__[1]
        inherits = cls._decl_class_registry.get(inherits.__name__, None)
        mapper_args = getattr(cls, '__mapper_args__', {})
        
        cls.__mapper__ = mapper(cls, table, inherits=inherits, properties=dict([(f.name, f) for f in our_stuff]), **mapper_args)
        cls.query = Session.query_property()
        return type.__init__(cls, classname, bases, dict_)
    
    def __setattr__(cls, key, value):
        if '__mapper__' in cls.__dict__:
            if isinstance(value, Column):
                cls.__table__.append_column(value)
                cls.__mapper__.add_property(key, value)
            elif isinstance(value, MapperProperty):
                cls.__mapper__.add_property(key, _deferred_relation(cls, value))
            elif isinstance(value, declared_synonym):
                value._setup(cls, key, None)
            else:
                type.__setattr__(cls, key, value)
        else:
            type.__setattr__(cls, key, value)

def _deferred_relation(cls, prop):
    if isinstance(prop, PropertyLoader) and isinstance(prop.argument, basestring):
        arg = prop.argument
        def return_cls():
            return cls._decl_class_registry[arg]
        prop.argument = return_cls

    return prop

class declared_synonym(object):
    def __init__(self, prop, name, mapperprop=None):
        self.prop = prop
        self.name = name
        self.mapperprop = mapperprop
        
    def _setup(self, cls, key, init_dict):
        prop = self.mapperprop or getattr(cls, self.name)
        prop = _deferred_relation(cls, prop)
        setattr(cls, key, self.prop)
        if init_dict is not None:
            init_dict[self.name] = prop
            init_dict[key] = _orm_synonym(self.name)
        else:
            setattr(cls, self.name, prop)
            setattr(cls, key, _orm_synonym(self.name))

class Model(models.Model):
    '''
    The base class for all entities    
    '''
    __metaclass__ = ModelBase
    
    metadata = metadata
    _decl_class_registry = {}
    def __init__(self, **kwargs):
        for k in kwargs:
            if not hasattr(type(self), k):
                raise TypeError('%r is an invalid keyword argument for %s' %
                                (k, type(self).__name__))
            setattr(self, k, kwargs[k])
        return super(Model, self).__init__(**kwargs)
