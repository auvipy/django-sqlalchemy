from django.db import models
from sqlalchemy import *
from sqlalchemy import ForeignKey as safk
from django_sqlalchemy.models.fields import Field

class ForeignKey(models.ForeignKey):
    def __init__(self, to, *args, **kwargs):
        self.column = None   
        models.ForeignKey.__init__(self, to, *args, **kwargs)
    
    def create_column(self):
        fk_primary = list(self.rel.to.__table__.primary_key)[0]
        self.column = Column('%s_%s' % (self.rel.to._meta.object_name.lower(), self.rel.to._meta.pk.name), 
                        fk_primary.type, safk(fk_primary))
        return self.column
