
from django_sqlalchemy import models

class Product(models.Model):
    name = models.CharField(max_length=18)
