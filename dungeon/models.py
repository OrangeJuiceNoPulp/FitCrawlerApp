from django.db import models

from gym.models import FitCrawlerUser

import datetime

# Create your models here.

STARTING_MAX_HEALTH = 20
STARTING_COINS = 0
STARTING_ACTION_POINTS = 0

class Dungeon(models.Model):
    # Columns
    name = models.CharField(max_length=127)
    description = models.CharField(max_length=511)
    
    # "width" is the amount of characters at which the dungeon layout wraps, to form a 2D array
    width = models.IntegerField()
    layout = models.TextField()
    
    def __str__(self):
        return str(self.name)
    

class DungeonExploration(models.Model):
    # Columns
    current_location = models.IntegerField()
    previous_location = models.IntegerField()
    direction = models.CharField(max_length=7)
    
    health = models.IntegerField()
    
    exploration_start = models.DateTimeField(default=datetime.datetime.now())
    
    user = models.ForeignKey(FitCrawlerUser, on_delete=models.CASCADE)
    dungeon = models.ForeignKey(Dungeon, on_delete=models.CASCADE)
    
    def __str__(self):
        return str(self.user) + ': ' + str(self.dungeon) 
    
class Sword(models.Model):
    # Columns
    # Lowest sword rank is 0
    sword_rank = models.IntegerField()
    name = models.CharField(max_length=63)
    strength_boost = models.FloatField()
    
    def __str__(self):
        return str(self.name) + ': ' + str(self.sword_rank) 
    
class Boots(models.Model):
    # Columns
    # Lowest boots rank is 0
    boots_rank = models.IntegerField()
    name = models.CharField(max_length=63)
    ap_reduction_factor = models.FloatField()
    
    def __str__(self):
        return str(self.name) + ': ' + str(self.boots_rank) 
    
class Staff(models.Model):
    # Columns
    # Lowest staff rank is 0
    staff_rank = models.IntegerField()
    name = models.CharField(max_length=63)
    healing_factor = models.FloatField()
    
    def __str__(self):
        return str(self.name) + ': ' + str(self.staff_rank) 
    
class Armor(models.Model):
    # Columns
    # Lowest armor rank is 0
    armor_rank = models.IntegerField()
    name = models.CharField(max_length=63)
    defense_factor = models.FloatField()
    
    def __str__(self):
        return str(self.name) + ': ' + str(self.armor_rank) 
    
class GameStats(models.Model):
    # Columns
    # PK is the same as the user's id
    user = models.OneToOneField(FitCrawlerUser, on_delete=models.CASCADE, related_name='game_stats', primary_key=True)
    
    # Game Stats
    max_health = models.IntegerField(default=STARTING_MAX_HEALTH)
    coins = models.BigIntegerField(default=STARTING_COINS)
    action_points = models.FloatField(default=STARTING_MAX_HEALTH)

    dungeons_completed = models.IntegerField(default=0)
    
    # Game Equipment
    sword = models.ForeignKey(Sword, on_delete=models.SET_NULL, null=True)
    boots = models.ForeignKey(Boots, on_delete=models.SET_NULL, null=True)
    staff = models.ForeignKey(Staff, on_delete=models.SET_NULL, null=True)
    armor = models.ForeignKey(Armor, on_delete=models.SET_NULL, null=True)
    
    

    def __str__(self):
        return str(self.user)
    
class Milestone(models.Model):
    # Columns
    
    # Milestone Requirements
    num_noob_task = models.IntegerField(default=0)
    num_easy_task = models.IntegerField(default=0)
    num_medium_task = models.IntegerField(default=0)
    num_hard_task = models.IntegerField(default=0)
    num_expert_task = models.IntegerField(default=0)
    
    total_minutes_walked = models.IntegerField(default=0)
    total_water_drank_L = models.FloatField(default=0)
    total_fruit_veggie_servings = models.IntegerField(default=0)

    total_dungeons_completed = models.IntegerField(default=0)
    
    # Milestone Rewards
    reward_action_points = models.IntegerField(default=0)
    reward_sword = models.ForeignKey(Sword, on_delete=models.SET_NULL, null=True, blank=True)
    reward_boots = models.ForeignKey(Boots, on_delete=models.SET_NULL, null=True, blank=True)
    reward_staff = models.ForeignKey(Staff, on_delete=models.SET_NULL, null=True, blank=True)
    reward_armor = models.ForeignKey(Armor, on_delete=models.SET_NULL, null=True, blank=True)
    reward_max_health = models.IntegerField(default=0)
    
    
class MilestoneLog(models.Model):
    # Columns
    milestone = models.ForeignKey(Milestone, on_delete=models.CASCADE)
    user = models.ForeignKey(FitCrawlerUser, on_delete=models.CASCADE)
    time_completed = models.DateTimeField(default=datetime.datetime.now())
    
    def __str__(self):
        return str(self.user) + ' - ' + str(self.time_completed)