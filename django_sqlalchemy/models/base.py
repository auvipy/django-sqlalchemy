
from django.db import models

from django_sqlalchemy.utils import ClassReplacer

class Model(object):
    __metaclass__ = ClassReplacer(models.Model)
    
    def save(self):
        raise NotImplemented()
    
    def delete(self):
        raise NotImplemented()
