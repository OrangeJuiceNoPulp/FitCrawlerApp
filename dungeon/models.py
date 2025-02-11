from django.db import models

# Create your models here.
from gym.models import FitCrawlerUser

# Create your models here.

class Dungeon(models.Model):
    # Columns
    name = models.CharField(max_length=127)
    description = models.CharField(max_length=511)
    
    # "width" is the amount of characters at which the dungeon layout wraps, to form a 2D array
    width = models.IntegerField()
    layout = models.TextField()
    

class DungeonExploration(models.Model):
    # Columns
    current_location = models.IntegerField()
    previous_location = models.IntegerField()
    direction = models.CharField(max_length=7)
    
    health = models.IntegerField()
    
    exploration_start = models.DateTimeField()
    
    user = models.ForeignKey(FitCrawlerUser, on_delete=models.CASCADE)
    dungeon = models.ForeignKey(Dungeon, on_delete=models.CASCADE)
    
class GameStats(models.Model):
    # Columns
    # PK is the same as the user's id
    user = models.OneToOneField(FitCrawlerUser, on_delete=models.CASCADE, related_name='game_stats', primary_key=True)
    max_health = models.IntegerField()
    coins = models.BigIntegerField()