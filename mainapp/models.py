from django.db import models
from django.contrib.postgres.fields import ArrayField

# Create your models here.

# Notes class
#class note(models.Model):
#  title = models.CharField(max_length=225,unique=True)
#  content = models.TextField()
#
#
## Youtube Video Class
#class video(models.Model):
#  url = models.URLField()
#  iscompleted = models.BooleanField(default=False)
#  notes = ArrayField(
#     model_container = note
#  )

# Learning Module Class
class Module(models.Model):
  title = models.CharField(max_length=50,unique=True)
  description = models.CharField(max_length=225)
  videosList = ArrayField(
    models.JSONField()
  )