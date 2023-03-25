from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.conf import settings

User = settings.AUTH_USER_MODEL

# Learning Module Class
class Module(models.Model):
  user = models.ForeignKey(User,
                        default = 1,
                        null = True,
                        on_delete = models.SET_NULL
                        )
  title = models.CharField(max_length=50,unique=True)
  description = models.CharField(max_length=225)
  videosList = ArrayField(
    models.JSONField()
  )