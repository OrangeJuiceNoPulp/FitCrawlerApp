from django.db import models
from django.utils.timezone import now

from gym.models import FitCrawlerUser

import datetime

# Create your models here.

STARTING_MAX_HEALTH = 20
STARTING_COINS = 0
STARTING_ACTION_POINTS = 0


    

class DungeonEnemy(models.Model):
    # Columns
    name = models.CharField(max_length=63)
    strength = models.FloatField()
    defense = models.FloatField()
    max_health = models.IntegerField()

    sprite_path = models.CharField(max_length=63, blank=True, null=True)

    def __str__(self):
        return str(self.name)
    
class Dungeon(models.Model):
    # Columns
    name = models.CharField(max_length=127)
    description = models.CharField(max_length=511)
    
    # "width" is the amount of characters at which the dungeon layout wraps, to form a 2D array
    width = models.IntegerField()
    layout = models.TextField()

    DIFFICULTIES = (('Noob', 'Noob'), ('Easy', 'Easy'), ('Medium', 'Medium'), ('Hard', 'Hard'), ('Expert', 'Expert'))
    difficulty_score = models.CharField(max_length=31, choices=DIFFICULTIES, default='Medium')
    # 1-2 Noob, 3-4 Easy, 5-6 Medium, 7-8 Hard, 9-10 Expert
    difficulty_quantifer = models.FloatField(default=5)

    sprite_folder = models.CharField(max_length=63, blank=True, null=True)
    thumbnail_path = models.CharField(max_length=63, blank=True, null=True)


    # Dungeon Encoding:
    #
    # S = start location
    # 1 through 9 = empty space (places where the player can move)
    # E = Dungeon End

    # 0 (zero) = always wall, o (lowercase O) = conditional wall
    wall_spawn = models.FloatField(default=1)

    # C = always spawn chest, c = conditional spawn
    chest_spawn = models.FloatField(default=1)


    # X = always spawn, x = conditional spawn
    common_monster = models.ForeignKey(DungeonEnemy, on_delete=models.SET_NULL, related_name='common', blank=True, null=True)
    common_monster_spawn = models.FloatField(default=1)

    # Y = always spawn, y = conditional spawn
    uncommon_monster = models.ForeignKey(DungeonEnemy, on_delete=models.SET_NULL, related_name='uncommon', blank=True, null=True)
    uncommon_monster_spawn = models.FloatField(default=1)

    # Z = always spawn, z = conditional spawn
    boss_monster = models.ForeignKey(DungeonEnemy, on_delete=models.SET_NULL, related_name='boss', blank=True, null=True)
    boss_monster_spawn = models.FloatField(default=1)

    def __str__(self):
        return str(self.name)
    

class DungeonExploration(models.Model):
    # Columns
    # PK is the same as the user's id
    user = models.OneToOneField(FitCrawlerUser, on_delete=models.CASCADE, related_name='dungeon_exploration', primary_key=True)

    current_location = models.IntegerField()
    previous_location = models.IntegerField()
    direction = models.CharField(max_length=7)
    
    health = models.FloatField()
    
    exploration_start = models.DateTimeField(default=now)
    
    dungeon = models.ForeignKey(Dungeon, on_delete=models.CASCADE)
    dungeon_layout = models.TextField()
    
    def __str__(self):
        return str(self.user) + ': ' + str(self.dungeon) 
    
    
class DungeonBattle(models.Model):
    exploration = models.OneToOneField(DungeonExploration, on_delete=models.CASCADE, related_name='dungeon_battle', primary_key=True)
    
    enemy = models.ForeignKey(DungeonEnemy, on_delete=models.CASCADE)
    enemy_health = models.FloatField()
    
    def __str__(self):
        return str(self.exploration) + ': ' + str(self.enemy) 
    
class Sword(models.Model):
    # Columns
    # Lowest sword rank is 0
    sword_rank = models.IntegerField()
    name = models.CharField(max_length=63)
    strength_boost = models.FloatField()
    sprite_path = models.CharField(max_length=63, blank=True, null=True)
    
    def __str__(self):
        return str(self.name) + ': ' + str(self.sword_rank) 
    
class Boots(models.Model):
    # Columns
    # Lowest boots rank is 0
    boots_rank = models.IntegerField()
    name = models.CharField(max_length=63)
    ap_reduction_factor = models.FloatField()
    sprite_path = models.CharField(max_length=63, blank=True, null=True)
    
    def __str__(self):
        return str(self.name) + ': ' + str(self.boots_rank) 
    
class Staff(models.Model):
    # Columns
    # Lowest staff rank is 0
    staff_rank = models.IntegerField()
    name = models.CharField(max_length=63)
    healing_factor = models.FloatField()
    sprite_path = models.CharField(max_length=63, blank=True, null=True)
    
    def __str__(self):
        return str(self.name) + ': ' + str(self.staff_rank) 
    
class Armor(models.Model):
    # Columns
    # Lowest armor rank is 0
    armor_rank = models.IntegerField()
    name = models.CharField(max_length=63)
    defense_factor = models.FloatField()
    sprite_path = models.CharField(max_length=63, blank=True, null=True)
    
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
    time_completed = models.DateTimeField(default=now)
    
    def __str__(self):
        return str(self.user) + ' - ' + str(self.time_completed)