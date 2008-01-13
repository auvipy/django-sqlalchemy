from django.db import models
from django_sqlalchemy.utils import ClassReplacer
from sqlalchemy import Column
from sqlalchemy.orm import deferred, synonym
from sqlalchemy.types import *
from sqlalchemy.ext.associationproxy import association_proxy

class Field(object):
    __metaclass__ = ClassReplacer(models.Field)
    
    def __init__(self, *args, **kwargs):
        self.synonym = kwargs.pop('synonym', None)
        self.deferred = kwargs.pop('deferred', False)
        
        self._original.__init__(self, *args, **kwargs)
        self.sa_column = None
        
    def create_sa_column(self):
        # create the base kwargs dict for sa
        kwargs = dict(key=self.column, nullable=self.null,
                index=self.db_index, unique=self.unique)
        # dump in field specific kwargs and overrides
        kwargs.update(self.sa_column_kwargs())
        self.sa_column = Column(self.name, self.sa_column_type(), 
                *self.sa_column_args(),
                **kwargs)
        self.entity._descriptor.add_column(self.column)

    def sa_column_type(self):
        raise NotImplementedError
    
    def sa_column_args(self):
        return tuple()
    
    def sa_column_kwargs(self):
        return dict()
        
class AutoField(Field):
    def sa_column_kwargs(self):
        kwargs = dict(primary_key=True)
        base = super(AutoField, self).sa_column_kwargs()
        base.update(kwargs)
        return base
        
    def sa_column_type(self):
        return Integer
        
class CharField(Field):
    def sa_column_kwargs(self):
        kwargs = dict()
        base = super(AutoField, self).sa_column_kwargs()
        base.update(kwargs)
        return base
        
    def sa_column_type(self):
        return Unicode(length=self.max_length)
        
