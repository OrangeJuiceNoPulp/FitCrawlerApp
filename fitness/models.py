from django.db import models

from exercises.models import Exercise
from gym.models import FitCrawlerUser

# Create your models here.

class Task(models.Model):
    # PK (id) is automatically handled by Django 
    # (Future models will not include these comments because I am tired of writing them each time.)
    
    DIFFICULTIES = (('Noob', 'Noob'), ('Easy', 'Easy'), ('Medium', 'Medium'), ('Hard', 'Hard'), ('Expert', 'Expert'))

    # Specify columns for the table in the database
    name = models.CharField(max_length=255)
    sets = models.IntegerField()
    difficulty_score = models.CharField(max_length=31, choices=DIFFICULTIES, default='Medium')
    num_per_set = models.IntegerField()
    days_of_week = models.CharField(max_length=15)
    end_date = models.DateTimeField(null=True)
    
    user = models.ForeignKey(FitCrawlerUser, on_delete=models.CASCADE)
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)
    
    def __str__(self):
        return str(self.user) + ': ' + str(self.exercise)
    
class Log(models.Model):
    # Columns
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    percent_completion = models.FloatField()
    time_completed = models.DateTimeField()
    
    def __str__(self):
        return str(self.task) + ' - ' + str(self.time_completed)