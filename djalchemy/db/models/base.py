from djalchemy.backend.base import metadata, Session, session
from djalchemy.db.models import *
from django.db.models import ModelBase
from sqlalchemy.schema import Table, Column
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


class ModelBase(ModelBase):
    def __new__(cls, name, bases, attrs):
        # For reasons I don't entirely understand, both __new__ and
        # __init__ can be called more than once. This seems to happen
        # when using __import__ in a way that doesn't trigger a hit in
        # sys.modules. So, for things like SA mapping and
        # session-ating, we need to be aware that this should only be
        # done the first time around.
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

        # we need to check if we've already created the AutoField.
        # AutoField here represents the dj-sa AutoField not Django's
        if not isinstance(cls._meta.pk, AutoField):
            # we need to add in the django-sqlalchemy version of the AutoField
            # because the one that Django adds will not work for our purposes.
            auto = AutoField(
                verbose_name='ID', primary_key=True, auto_created=True)
            # this might seem redundant but without it the name is not set 
            # for SA
            auto.name = "id"
            # now we can append the AutoField into our_stuff which gets
            # used in the SA Table declaration
            our_stuff.append(auto.create_column())
        for field in cls._meta.fields:
            from django_sqlalchemy.models.fields.related import ForeignKey
            # Field and ForeignKey here are our implementations of
            # those fields.  It's specifically done that way to ignore
            # things like Django's AutoField.
            if isinstance(field, (Field, ForeignKey)):
                our_stuff.append(field.create_column())

        # SA supports autoloading the model from database, but that will
        # not work for Django. We're leaving this here just for future
        # consideration.
        autoload = cls.__dict__.get('__autoload__')
        if autoload:
            table_kw = {'autoload': True}
        else:
            table_kw = {}

        # this sets up the Table declaration and also adds it as an __table__
        # attribute on our model class.
        if not cls._meta.db_table in cls.metadata:
            cls.__table__ = table = Table(
                cls._meta.db_table, cls.metadata, *our_stuff, **table_kw)
        else:
            # `table' is also assigned above.
            table = cls.__table__

        inherits = cls.__mro__[1]
        inherits = cls._decl_class_registry.get(inherits.__name__, None)
        mapper_args = getattr(cls, '__mapper_args__', {})

        # finally we add the SA Mapper declaration, if we haven't been
        if not hasattr(cls, "__mapper__"):
            cls.__mapper__ = mapper(
                cls, table, inherits=inherits,
                properties=dict([(f.name, f) for f in our_stuff]),
                **mapper_args
            )
        # add the SA Query class onto our model class for easy querying
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


class declared_synonym:
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

    def save(self):
        """
        Save the current instance. We force a flush so it mimics Django's
        behavior.
        """
        if self.pk is None:
            obj = session.save(self)
            session.commit()
        else:
            obj = self.update()
        return obj

    def update(self, *args, **kwargs):
        """
        Updates direct against the database
        """
        obj = session.update(self, *args, **kwargs)
        session.commit()
        return obj

    def delete(self):
        """
        Deletes the current instance
        """
        obj = session.delete(self)
        session.commit()
        return obj
