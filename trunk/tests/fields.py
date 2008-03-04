from utils import ClassReplacer, MethodContainer
import sys
from maxlength import LegacyMaxlength
from partial import *

# models.Field
class BaseClass(object):
    __metaclass__ = LegacyMaxlength

    creation_counter = 0    
    
    def __init__(self, verbose_name=None, name=None, primary_key=False,
        max_length=None, unique=False, blank=False, null=False, db_index=False,
        core=False, rel=None, default=None, editable=True, serialize=True,
        unique_for_date=None, unique_for_month=None, unique_for_year=None,
        validator_list=None, choices=None, radio_admin=None, help_text='', db_column=None,
        db_tablespace=None):
        print "BaseClass.__init__ called"
        self.name = name
        self.verbose_name = verbose_name
        self.primary_key = primary_key
        self.max_length, self.unique = max_length, unique
        self.blank, self.null = blank, null
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
        self.db_tablespace = db_tablespace
        
        # Set db_index to True if the field has a relationship and doesn't explicitly set db_index.
        self.db_index = db_index
        
        # Increase the creation counter, and save our local copy.
        self.creation_counter = BaseClass.creation_counter
        BaseClass.creation_counter += 1

    def method1(self):
        print "BaseClass.method1 called"

# models.AutoField
class DerivedClass(BaseClass):
    def __init__(self, *args, **kwargs):
        print "DerivedClass.__init__ called"
        kwargs['blank'] = True
        BaseClass.__init__(self, *args, **kwargs)
    
    def method1(self):
        print "DerivedClass.method1 called"
        super(DerivedClass, self).method1()

# django_sqlalchemy.models.Field
class MyBaseClass(object):
    __metaclass__ = ClassReplacer(BaseClass)
    
    def method4(self):
        print "MyBaseClass.method4 called"
        
    def testcall(self):
        return self.method5()
    
    def method5(self):
        print "MyBaseClass.method5 called"

# django_sqlalchemy.models.AutoField
class MyDerivedClass(object):
    __metaclass__ = ClassReplacer(DerivedClass)
    
    def method2(self):
        print "MyDerivedClass.method2 called"

    def method5(self):
        print "MyDerivedClass.method5 called"


field = MyDerivedClass()
field.method1()
field.method2()
field.method4()
field.testcall()
field.primary_key