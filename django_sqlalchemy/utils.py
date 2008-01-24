import pdb

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
    
    >>> baseclass_instance = BaseClass()
    BaseClass.__init__ called
    >>> baseclass_instance.method1()
    BaseClass.method1 called
    
    >>> class MyMetaclass(type):
    ...     __metaclass__ = ClassReplacer(BaseMetaclass)
    ...     def __new__(cls, name, bases, attrs):
    ...         print "MyMetaclass.__new__ called"
    ...         return self._original.__new__(cls, name, bases, attrs)
    
    >>> class MyClass(object):
    ...     __metaclass__ = ClassReplacer(BaseClass)
    ...     
    ...     def __init__(self):
    ...         print "MyClass.__init__ called"
    ...         self._original.__init__(self)
    ...     
    ...     def method2(self):
    ...         print "MyClass.method2 called"
    MyMetaclass.__new__ called
    BaseMetaclass.__new__ called
    
    >>> myclass_instance = MyClass()
    MyClass.__init__ called
    BaseClass.__init__ called
    >>> myclass_instance.method2()
    MyClass.method2 called
    >>> myclass_instance.method1()
    BaseClass.method1 called
    """
    
    def __init__(self, klass, metaclass=None):
        self.klass = klass
        self.metaclass = metaclass
    
    def __call__(self, name, bases, attrs):
        for n, v in attrs.items():
            if n in ("__class__", "__bases__", "__module__"):
                continue
            if n == "__metaclass__" and self.metaclass:
                setattr(self.klass, "__metaclass__", self.metaclass(self.klass.__class__.__name__, (), {}))
            else:
                # if the attribute exists in the original class then stuff it in the _original inner class 
                setattr(self.klass, "_original", MethodContainer())
                if hasattr(self.klass, n):
                    setattr(self.klass._original, n, getattr(self.klass, n))
                # add the attribute to the original class
                setattr(self.klass, n, v)
        return self.klass



def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    _test()
