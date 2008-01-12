
class MethodContainer(object):
    pass

class ClassReplacer(object):
    """
    Acts as a metaclass to replace the given class with the metaclass class.
    An improved version originally found in the sadjango project.
    
    Create the base metaclass and base class.
    
    >>> class BaseMetaclass(type):
    ...     def __new__(cls, name, bases, attrs):
    ...         print "BaseMetaclass.__new__ called"
    ...         return super(BaseMetaclass, cls).__new__(cls, name, bases, attrs)

    >>> class BaseClass(object):
    ...     __metaclass__ = BaseMetaclass
    ...
    ...     def __init__(self):
    ...         print "BaseClass.__init__ called"
    ...
    ...     def method1(self):
    ...         print "BaseClass.method1 called"
    BaseMetaclass.__new__ called
    
    >>> class MyMetaclass(type):
    ...     def __new__(cls, name, bases, attrs):
    ...         print "MyMetaclass.__new__ called"
    ...         return super(MyMetaclass, cls).__new__(cls, name, bases, attrs)
    
    >>> class MyClass(object):
    ...     __metaclass__ = ClassReplacer(BaseClass, MyMetaclass)
    ...
    ...     def __init__(self):
    ...         print "MyClass.__init__ called"
    ...         self._original.__init__(self)
    ...
    ...     def method2(self):
    ...         print "MyClass.method2 called"
    
    >>> BaseClass.__metaclass__
    <class '__main__.MyMetaclass'>
    
    >>> class SubClass(BaseClass):
    ...     def __init__(self):
    ...         super(SubClass, self).__init__()
    ...         print "SubClass.__init__ called"
    ...
    ...     def method3(self):
    ...         print "SubClass.method3 called"
    MyMetaclass.__new__ called
    
    >>> instance = SubClass()
    MyClass.__init__ called
    BaseClass.__init__ called
    SubClass.__init__ called
    
    >>> instance.method3()
    SubClass.method3 called
    
    >>> myclass_instance = MyClass()
    MyClass.__init__ called
    BaseClass.__init__ called
    >>> myclass_instance.method2()
    MyClass.method2 called
    
    >>> baseclass_instance = BaseClass()
    MyClass.__init__ called
    BaseClass.__init__ called
    >>> baseclass_instance.method1()
    BaseClass.method1 called
    """
    
    def __init__(self, klass, metaclass=None):
        self.klass = klass
        self.metaclass = metaclass
    
    def __call__(self, name, bases, attrs):
        for name, value in attrs.items():
            if name in ("__class__", "__bases__", "__module__"):
                continue
            if name == "__metaclass__":
                setattr(self.klass, "__metaclass__", self.metaclass)
            else:
                setattr(self.klass, "_original", MethodContainer())
                if hasattr(self.klass, name):
                    setattr(self.klass._original, name, getattr(self.klass, name))
                setattr(self.klass, name, value)
        return self.klass

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    _test()
