import datetime
from django_sqlalchemy import models

# Create your models here.
class Category(models.Model):
    """Category Class"""
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(default=datetime.datetime.now)
    
    def __unicode__(self):
        return self.name
    
class Post(models.Model):
    pub_date = models.DateTimeField(default=datetime.datetime.now)
    category = models.ForeignKey(Category)
    body = models.TextField(blank=True)
    
    def __unicode__(self):
        return self.body
