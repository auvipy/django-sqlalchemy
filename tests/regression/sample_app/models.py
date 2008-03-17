from django_sqlalchemy import models

class Publisher(models.Model):
    username = models.CharField(max_length=32)
    


