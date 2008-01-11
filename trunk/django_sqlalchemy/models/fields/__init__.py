
from django.db import models

from django_sqlalchemy.utils import ClassReplacer

class Field(object):
    __metaclass__ = ClassReplacer(models.Field)
    
    def __init__(self, *args, **kwargs):
        print "i am in your classz stealin your methodz"
        self._original.__init__(self, *args, **kwargs)
