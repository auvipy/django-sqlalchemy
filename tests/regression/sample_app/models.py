from djalchemy import models

class Reporter(models.Model):
    username = models.CharField(max_length=32)
    
class Source(models.Model):
    class Meta:
        db_table = "sources"
    codename = models.CharField(max_length=32, null=False, default="Deep Throat")

class Article(models.Model):
    class Meta:
        db_table = "articles"
    sources = models.ManyToManyField(Source, related_name="stories")
    author = models.ForeignKey(Reporter, related_name="stories")
    content = models.TextField()
    
