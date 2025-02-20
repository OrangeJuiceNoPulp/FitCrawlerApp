from django.db import models

# Create your models here.

class Exercise(models.Model):
    # Columns
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=511)
    
    def __str__(self):
        return str(self.name)
    
class ExerciseVideo(models.Model):
    # Columns
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)
    video_link = models.URLField(max_length=255)
