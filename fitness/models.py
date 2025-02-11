from django.db import models

from exercises.models import Exercise
from gym.models import FitCrawlerUser

# Create your models here.

class Task(models.Model):
    # PK (id) is automatically handled by Django 
    # (Future models will not include these comments because I am tired of writing them each time.)
    
    # Specify columns for the table in the database
    name = models.CharField(max_length=255)
    sets = models.IntegerField()
    num_per_set = models.IntegerField()
    days_of_week = models.CharField(max_length=15)
    
    user = models.ForeignKey(FitCrawlerUser, on_delete=models.CASCADE)
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)
    
class Log(models.Model):
    # Columns
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    percent_completion = models.FloatField()
    time_completed = models.DateTimeField()