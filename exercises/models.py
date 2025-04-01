import re
from django.db import models

# Create your models here.

class Exercise(models.Model):
    # Columns
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=511)
    video_link = models.URLField(null=True, blank=True, max_length=255, default=None)
    
    def __str__(self):
        return str(self.name)
    
