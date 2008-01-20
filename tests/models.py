from django_sqlalchemy.utils import ClassReplacer, MethodContainer
import sys
import pdb

# django.db.models.base.ModelBase
class BaseMetaclass(type):
    def __new__(cls, name, bases, attrs):
         print "BaseMetaclass.__new__ called"
         return super(BaseMetaclass, cls).__new__(cls, name, bases, attrs)

# django.db.models.base.Model
class BaseClass(object):
    __metaclass__ = BaseMetaclass

    def __init__(self):
        print "BaseClass.__init__ called"
        return super(BaseClass, self).__init__(self)
    
    def method1(self):
        print "BaseClass.method1 called"

# django_sqlalchemy.models.base.ModelBase
class MyMetaclass(type):
    __metaclass__ = BaseMetaclass
    
    def __init__(cls, name, bases, attrs):
        print "MyMetaclass.__init__ called"
        cls._descriptor = 35

# django_sqlalchemy.models.base.Model        
class MyClass(object):
    __metaclass__ = ClassReplacer(BaseClass, MyMetaclass)
    
    def __init__(self):
        print "MyClass.__init__ called"
        
    def method2(self):
        print "MyClass.method2 called"
        
myclass_instance = MyClass()
print myclass_instance.__metaclass__
myclass_instance.method2()
myclass_instance.method1()
print myclass_instance._descriptor