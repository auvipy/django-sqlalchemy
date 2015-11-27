from django.db import models
import sqlalchemy as sa


class ForeignKey(models.ForeignKey):
    def __init__(self, to, *args, **kwargs):
        self.column = None   
        models.ForeignKey.__init__(self, to, *args, **kwargs)
    
    def create_column(self):
        # ForeignKey will be shadowed by the class inside of this method.
        from sqlalchemy import ForeignKey as safk
        fk_primary = list(self.rel.to.__table__.primary_key)[0]
        self.column = sa.Column('%s_%s' % (
            self.rel.to._meta.object_name.lower(),
            self.rel.to._meta.pk.name), 
                             fk_primary.type, safk(fk_primary))
        return self.column

class ManyToManyField(models.ManyToManyField):
    def __init__(self, to, *args, **kwargs):
        super(self.__class__, self).__init__(to, *args, **kwargs)

    def add(self, *args, **kwargs):
        super(self.__class__, self).add(self, *args, **kwargs)
        from django_sqlalchemy.backend.base import Session
        Session.commit()
            
            
        
    def contribute_to_class(self, cls, related):
        from django_sqlalchemy.backend.base import metadata
        super(self.__class__, self).contribute_to_class(cls, related)
        tbl_name = self.m2m_db_table()
        # Apparently, inclusion in metadata checks for table names. 
        if not tbl_name in metadata:
            # In which case, we create it. 
            local_m2m_col = self.m2m_column_name()
            remote_m2m_col = self.m2m_reverse_name()
            import sqlalchemy as sa
            joining_table = sa.Table(
                tbl_name, metadata,
                # HACKity hackity hack hack hack, we need to use the
                # correct type here. A foreign key would be nice too.
                sa.Column(local_m2m_col, sa.Integer, ),
                sa.Column(remote_m2m_col, sa.Integer, ),)
            joining_table.create(metadata.bind)
        # Now, what I don't get is why this path being called more
        # than once for the same tbl_name.
        
            
                   
                   
        
