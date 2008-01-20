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
                index=self.db_index, unique=self.unique, default=self.default)
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
    __metaclass__ = ClassReplacer(models.AutoField)
    def sa_column_kwargs(self):
        kwargs = dict(primary_key=True)
        base = super(AutoField, self).sa_column_kwargs()
        base.update(kwargs)
        return base
    
    def sa_column_type(self):
        return Integer()

class BooleanField(Field):
    __metaclass__ = ClassReplacer(models.BooleanField)
    def sa_column_type(self):
        return Boolean()
    
class CharField(Field):
    __metaclass__ = ClassReplacer(models.CharField)
    def sa_column_type(self):
        return Unicode(length=self.max_length)
        
class CommaSeparatedIntegerField(CharField):
    __metaclass__ = ClassReplacer(models.CommaSeparatedIntegerField)
    pass
    
class DateField(Field):
    __metaclass__ = ClassReplacer(models.DateField)
    def sa_column_type(self):
        return Date()

class DateTimeField(DateField):
    __metaclass__ = ClassReplacer(models.DateTimeField)
    def sa_column_type(self):
        return DateTime()

class DecimalField(Field):
    __metaclass__ = ClassReplacer(models.DecimalField)
    def sa_column_kwargs(self):
        kwargs = dict(precision=self.decimal_places, length=self.max_digits)
        base = super(AutoField, self).sa_column_kwargs()
        base.update(kwargs)
        return base

    def sa_column_type(self):
        return Numeric()

class EmailField(CharField):
    __metaclass__ = ClassReplacer(models.EmailField)
    pass
    
class FileField(Field):
    __metaclass__ = ClassReplacer(models.FileField)
    def sa_column_type(self):
        return Unicode(length=self.max_length)

class FilePathField(Field):
    __metaclass__ = ClassReplacer(models.FilePathField)
    def sa_column_type(self):
        return Unicode(length=self.max_length)

class FloatField(Field):
    __metaclass__ = ClassReplacer(models.FloatField)
    def sa_column_type(self):
        return Float()

class ImageField(FileField):
    __metaclass__ = ClassReplacer(models.ImageField)
    pass

class IntegerField(Field):
    __metaclass__ = ClassReplacer(models.IntegerField)
    def sa_column_type(self):
        return Integer()

class IPAddressField(Field):
    __metaclass__ = ClassReplacer(models.IPAddressField)
    def sa_column_type(self):
        return Unicode(length=self.max_length)

class NullBooleanField(Field):
    __metaclass__ = ClassReplacer(models.NullBooleanField)
    def sa_column_type(self):
        return Boolean()

class PhoneNumberField(Integer):
    __metaclass__ = ClassReplacer(models.PhoneNumberField)
    def sa_column_type(self):
        ''' This is a bit odd because in Django the PhoneNumberField descends from an IntegerField in a 
            hacky way of getting around not providing a max_length.  The database backends enforce the
            length as a varchar(20).
        '''
        return Unicode(length=20)

class PositiveIntegerField(IntegerField):
    __metaclass__ = ClassReplacer(models.PositiveIntegerField)
    pass
    
class PositiveSmallIntegerField(IntegerField):
    __metaclass__ = ClassReplacer(models.PositiveSmallIntegerField)
    def sa_column_type(self):
        return SmallInteger()

class SlugField(CharField):
    __metaclass__ = ClassReplacer(models.SlugField)
    pass

class SmallIntegerField(IntegerField):
    __metaclass__ = ClassReplacer(models.SmallIntegerField)
    def sa_column_type(self):
        return SmallInteger()

class TextField(Field):
    __metaclass__ = ClassReplacer(models.TextField)
    def sa_column_type(self):
        return UnicodeText()

class TimeField(Field):
    __metaclass__ = ClassReplacer(models.TimeField)
    def sa_column_type(self):
        return Time()

class URLField(CharField):
    __metaclass__ = ClassReplacer(models.URLField)
    pass

class USStateField(Field):
    __metaclass__ = ClassReplacer(models.USStateField)
    def sa_column_type(self):
        return Unicode(length=2)

class XMLField(TextField):
    __metaclass__ = ClassReplacer(models.XMLField)
    pass
    
class OrderingField(IntegerField):
    __metaclass__ = ClassReplacer(models.OrderingField)
    pass
