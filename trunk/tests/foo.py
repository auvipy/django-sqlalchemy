import sys
import pdb

# django.db.models.base.ModelBase
class BaseMetaclass(type):
    def __new__(cls, name, bases, attrs):
        print "BaseMetaclass.__new__ called"
        return super(BaseMetaclass, cls).__new__(cls, name, bases, attrs)
         
    def __call__(cls, *args, **kwargs):
        print "BaseMetaclass.__call__ called"
        return type.__call__(cls)

    def method4(cls):
        print "BaseMetaclass.method4 called"
 
# django.db.models.base.Model
class BaseClass(object):
    __metaclass__ = BaseMetaclass

    def __init__(self):
        print "BaseClass.__init__ called"
    
    def method3(self):
        print "BaseClass.method3 called"

# django_sqlalchemy.models.base.ModelBase
class MyMetaclass(BaseMetaclass):
    
    def __init__(cls, name, bases, attrs):
        print "MyMetaclass.__init__ called"
        return super(MyMetaclass, cls).__init__(cls, name, bases, attrs)
        
    def __call__(cls, *args, **kwargs):
        print "MyMetaclass.__call__ called"
        return super(MyMetaclass, cls).__call__(cls, *args, **kwargs)
        
    def method1(cls):
        print "MyMetaclass.method1 called"
 
# django_sqlalchemy.models.base.Model        
class MyClass(BaseClass):
    __metaclass__ = MyMetaclass

    def __init__(self):
        print "MyClass.__init__ called"
        return super(MyClass, self).__init__()
        
    def method2(self):
        print "MyClass.method2 called"
        
print "Starting Code >>>>"
myclass_instance = MyClass()
# print myclass_instance.__metaclass__
myclass_instance.method2()
myclass_instance.method3()
MyClass.method4()
MyClass.method1()