import sys

class A(object):
    def __init__(self):
        print "A.__init__ called"
        self.name = "a"
    
    def method3(self):
        print "A.method3 called"

class B(object):
    def __init__(self):
        print "B.__init__ called"
        self.name = "b"
    
    def method2(self):
        print "B.method2 called"
        
class C(B, A):
    def __init__(self):
        print "C.__init__ called"
        A.__init__(self)
        B.__init__(self)
    
    def method1(self):
        print "C.method1 called"
        print self.name

    def method3(self):
        print "C.method3 called"
        super(C, self).method3()

c = C()
c.method1()
c.method2()
c.method3()
