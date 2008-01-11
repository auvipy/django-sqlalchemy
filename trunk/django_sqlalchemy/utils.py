
class MethodContainer(object):
    pass

class ClassReplacer(object):
    """
    Acts as a metaclass to replace the given class with the metaclass class.
    An improved version originally found in the sadjango project.
    """
    def __init__(self, klass):
        self.klass = klass
    
    def __call__(self, name, bases, attrs):
        for name, value in attrs.items():
            if name in ("__class__", "__bases__", "__metaclass__", "__module__"):
                continue
            setattr(self.klass, "_original", MethodContainer())
            if hasattr(self.klass, name):
                setattr(self.klass._original, name, getattr(self.klass, name))
            setattr(self.klass, name, value)
        return self.klass

if __name__ == "__main__":
    # TODO: move tests to tests and write more tests :)
    class Field(object):
        def my_method(self):
            print "original MyClass::my_method"
    
    class Field(object):
        __metaclass__ = ClassReplacer(Field)
        
        def my_new_method(self):
            print "new MyClass::my_new_method"
        
        def my_method(self):
            print "new MyClass::my_method"
    
    class CharField(Field):
        def my_method(self):
            super(CharField, self).my_method()
            print "charfield my_method"
    
    cf = CharField()
    cf.my_method()
