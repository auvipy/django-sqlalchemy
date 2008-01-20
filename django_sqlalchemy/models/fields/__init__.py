from django.db import models
from django.conf import settings
from django_sqlalchemy.utils import ClassReplacer
from sqlalchemy import Column
from sqlalchemy.orm import deferred, synonym
from sqlalchemy.types import *
from sqlalchemy.ext.associationproxy import association_proxy
import pdb

class Field(object):
    __metaclass__ = ClassReplacer(models.Field)
    
    def django_field__init__(self, verbose_name=None, name=None, primary_key=False,
        max_length=None, unique=False, blank=False, null=False, db_index=False,
        core=False, rel=None, default=models.NOT_PROVIDED, editable=True, serialize=True,
        unique_for_date=None, unique_for_month=None, unique_for_year=None,
        validator_list=None, choices=None, radio_admin=None, help_text='', db_column=None,
        db_tablespace=None):
        self.name = name
        self.verbose_name = verbose_name
        self.primary_key = primary_key
        self.max_length, self.unique = max_length, unique
        self.blank, self.null = blank, null
        # Oracle treats the empty string ('') as null, so coerce the null
        # option whenever '' is a possible value.
        if self.empty_strings_allowed and settings.DATABASE_ENGINE == 'oracle':
            self.null = True
        self.core, self.rel, self.default = core, rel, default
        self.editable = editable
        self.serialize = serialize
        self.validator_list = validator_list or []
        self.unique_for_date, self.unique_for_month = unique_for_date, unique_for_month
        self.unique_for_year = unique_for_year
        self._choices = choices or []
        self.radio_admin = radio_admin
        self.help_text = help_text
        self.db_column = db_column
        self.db_tablespace = db_tablespace or settings.DEFAULT_INDEX_TABLESPACE

        # Set db_index to True if the field has a relationship and doesn't explicitly set db_index.
        self.db_index = db_index

        # Increase the creation counter, and save our local copy.
        self.creation_counter = Field.creation_counter
        Field.creation_counter += 1
        
    def __init__(self, *args, **kwargs):
        super(Field, self).__init__()
        
        self.synonym = kwargs.pop('synonym', None)
        self.deferred = kwargs.pop('deferred', False)
        # call django's init. this is here because I cannot figure out how to call django's Field.__init__
        # due to the way the maxlength metaclass is wired up.  it does crazy things, calling back to the 
        # derived class causing an infinite loop.
        # pdb.set_trace()
        self.django_field__init__(self, kwargs)
        
        self.colname = self.name
        self.column = None
        self.property = None
    
    def attach(self, entity, name):
        # If no colname was defined (through the 'colname' kwarg), set
        # it to the name of the attr.
        if self.colname is None:
            self.colname = name
        super(Field, self).attach(entity, name)
    
    def create_pk_cols(self):
        if self.primary_key:
            self.create_col()
    
    def create_non_pk_cols(self):
        if not self.primary_key:
            self.create_col()
    
    def create_col(self):
        # create the base kwargs dict for sa
        kwargs = dict(nullable=self.null,
                index=self.db_index, unique=self.unique, default=self.default)
        # dump in field specific kwargs and overrides
        kwargs.update(self.sa_column_kwargs())
        self.column = Column(self.name, self.sa_column_type(), 
                *self.sa_column_args(),
                **kwargs)
        self.entity._descriptor.add_column(self.column)
        
    def create_properties(self):
        if self.deferred:
            group = None
            if isinstance(self.deferred, basestring):
                group = self.deferred
            self.property = deferred(self.column, group=group)
        elif self.name != self.colname:
            self.property = self.column

        if self.property:
            self.entity._descriptor.add_property(self.name, self.property)

        if self.synonym:
            self.entity._descriptor.add_property(self.synonym, 
                                                 synonym(self.name))
    
    def sa_column_type(self):
        raise NotImplementedError
    
    def sa_column_args(self):
        return tuple()
    
    def sa_column_kwargs(self):
        return dict()
       
class AutoField(object):
    __metaclass__ = ClassReplacer(models.AutoField)
    
    def sa_column_kwargs(self):
        kwargs = dict(primary_key=True)
        base = super(AutoField, self).sa_column_kwargs()
        base.update(kwargs)
        return base
    
    def sa_column_type(self):
        return Integer()

class BooleanField(object):
    __metaclass__ = ClassReplacer(models.BooleanField)
    def sa_column_type(self):
        return Boolean()
    
class CharField(object):
    __metaclass__ = ClassReplacer(models.CharField)

    def __init__(self, *args, **kwargs):
        self._original.__init__(self, *args, **kwargs)
    
    def sa_column_type(self):
        return Unicode(length=self.max_length)
        
class CommaSeparatedIntegerField(object):
    __metaclass__ = ClassReplacer(models.CommaSeparatedIntegerField)
    pass
    
class DateField(object):
    __metaclass__ = ClassReplacer(models.DateField)
    def sa_column_type(self):
        return Date()

class DateTimeField(object):
    __metaclass__ = ClassReplacer(models.DateTimeField)
    def sa_column_type(self):
        return DateTime()

class DecimalField(object):
    __metaclass__ = ClassReplacer(models.DecimalField)
    def sa_column_kwargs(self):
        kwargs = dict(precision=self.decimal_places, length=self.max_digits)
        base = super(AutoField, self).sa_column_kwargs()
        base.update(kwargs)
        return base

    def sa_column_type(self):
        return Numeric()

class EmailField(object):
    __metaclass__ = ClassReplacer(models.EmailField)
    pass
    
class FileField(object):
    __metaclass__ = ClassReplacer(models.FileField)
    def sa_column_type(self):
        return Unicode(length=self.max_length)

class FilePathField(object):
    __metaclass__ = ClassReplacer(models.FilePathField)
    def sa_column_type(self):
        return Unicode(length=self.max_length)

class FloatField(object):
    __metaclass__ = ClassReplacer(models.FloatField)
    def sa_column_type(self):
        return Float()

class ImageField(object):
    __metaclass__ = ClassReplacer(models.ImageField)
    pass

class IntegerField(object):
    __metaclass__ = ClassReplacer(models.IntegerField)
    def sa_column_type(self):
        return Integer()

class IPAddressField(object):
    __metaclass__ = ClassReplacer(models.IPAddressField)
    def sa_column_type(self):
        return Unicode(length=self.max_length)

class NullBooleanField(object):
    __metaclass__ = ClassReplacer(models.NullBooleanField)
    def sa_column_type(self):
        return Boolean()

class PhoneNumberField(object):
    __metaclass__ = ClassReplacer(models.PhoneNumberField)
    
    def __init__(self, *args, **kwargs):
        self._original.__init__(self, *args, **kwargs)
    
    def sa_column_type(self):
        ''' This is a bit odd because in Django the PhoneNumberField descends from an IntegerField in a 
            hacky way of getting around not providing a max_length.  The database backends enforce the
            length as a varchar(20).
        '''
        return Unicode(length=20)

class PositiveIntegerField(object):
    __metaclass__ = ClassReplacer(models.PositiveIntegerField)
    pass
    
class PositiveSmallIntegerField(object):
    __metaclass__ = ClassReplacer(models.PositiveSmallIntegerField)
    def sa_column_type(self):
        return SmallInteger()

class SlugField(object):
    __metaclass__ = ClassReplacer(models.SlugField)
    pass

class SmallIntegerField(object):
    __metaclass__ = ClassReplacer(models.SmallIntegerField)
    def sa_column_type(self):
        return SmallInteger()

class TextField(object):
    __metaclass__ = ClassReplacer(models.TextField)
    def sa_column_type(self):
        return UnicodeText()

class TimeField(object):
    __metaclass__ = ClassReplacer(models.TimeField)
    def sa_column_type(self):
        return Time()

class URLField(object):
    __metaclass__ = ClassReplacer(models.URLField)
    pass

class USStateField(object):
    __metaclass__ = ClassReplacer(models.USStateField)
    def sa_column_type(self):
        return Unicode(length=2)

class XMLField(object):
    __metaclass__ = ClassReplacer(models.XMLField)
    pass
    
class OrderingField(object):
    __metaclass__ = ClassReplacer(models.OrderingField)
    pass
