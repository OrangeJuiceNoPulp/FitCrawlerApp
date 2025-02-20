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
    
class ExerciseVideo(models.Model):
    # Columns
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)
    video_link = models.URLField(max_length=255)

    def get_video_id(self):
        """Extract the YouTube video ID from the stored URL."""
        match = re.search(r"v=([a-zA-Z0-9_-]+)", self.video_link)
        return match.group(1) if match else None
