from django_sqlalchemy.models import *
from django.db import models
from sqlalchemy.schema import Table, SchemaItem, Column, MetaData
from sqlalchemy.orm import synonym as _orm_synonym, mapper
from sqlalchemy.orm.interfaces import MapperProperty
from sqlalchemy.orm.properties import PropertyLoader

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
        our_stuff = {}
        for k in dict_:
            value = dict_[k]
            if not isinstance(value, (Column, MapperProperty, declared_synonym)):
                continue
            if isinstance(value, declared_synonym):
                value._setup(cls, k, our_stuff)
            else:
                prop = _deferred_relation(cls, value)
                our_stuff[k] = prop
        
        table = None
        if '__table__' not in cls.__dict__:
            if '__tablename__' in cls.__dict__:
                tablename = cls.__tablename__
                autoload = cls.__dict__.get('__autoload__')
                if autoload:
                    table_kw = {'autoload': True}
                else:
                    table_kw = {}
                cls.__table__ = table = Table(tablename, cls.metadata, *[
                    c for c in our_stuff.values() if isinstance(c, Column)
                ], **table_kw)
        else:
            table = cls.__table__
        
        inherits = cls.__mro__[1]
        inherits = cls._decl_class_registry.get(inherits.__name__, None)
        mapper_args = getattr(cls, '__mapper_args__', {})
        
        cls.__mapper__ = mapper(cls, table, inherits=inherits, properties=our_stuff, **mapper_args)
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
    
    import pdb
    pdb.set_trace()
    
    metadata = metadata
    _decl_class_registry = {}
    def __init__(self, **kwargs):
        for k in kwargs:
            if not hasattr(type(self), k):
                raise TypeError('%r is an invalid keyword argument for %s' %
                                (k, type(self).__name__))
            setattr(self, k, kwargs[k])
        return super(Model, self).__init__(**kwargs)
