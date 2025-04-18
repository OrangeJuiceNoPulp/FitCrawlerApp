from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, connection

from fitness.views import check_and_create_game_stats, TASK_COMPLETION_REQUIREMENT

from django.urls import reverse
from urllib.parse import urlencode

import datetime
import random
import math

# Create your views here.

MOVEMENT_AP_BASE_COST = 5

ATTACK_AP_BASE_COST = 2

ESCAPE_AP_BASE_COST = 5

HEAL_BASE_COST = 3.5

BASE_HEAL_AMOUNT = 5

BASE_DAMAGE_AMOUNT = 0
BASE_DEFENSE_AMOUNT = 0

BASE_BATTLE_REWARD = 5
BASE_CHEST_REWARD = 25

# Helper function for rewarding the player for opening a chest
# - Jason 3/31/25
def chest_reward(user_id, difficulty_level):
    reward_amount = (BASE_CHEST_REWARD * difficulty_level)
    
    with connection.cursor() as cursor:
        cursor.execute("""
            UPDATE dungeon_gamestats
            SET coins = (coins + %s)
            WHERE user_id = %s
            """, [reward_amount,user_id])
    
    return reward_amount

# Helper function for rewarding the player for defeating an enemy
# - Jason 3/31/25
def battle_reward(user_id, enemy_type, difficulty_level):
    multiplier = 1
    if enemy_type == 'Y':
        multiplier = 2
    elif enemy_type == 'Z':
        multiplier = 3
    
    reward_amount = (BASE_BATTLE_REWARD * multiplier) + (2 * difficulty_level)
    
    with connection.cursor() as cursor:
        cursor.execute("""
            UPDATE dungeon_gamestats
            SET coins = (coins + %s)
            WHERE user_id = %s
            """, [reward_amount,user_id])
    
    return reward_amount

# Helper function for getting player inventory contents
# - Jason 3/16/25
def get_player_inventory(id):
    player_inventory = {}
    with connection.cursor() as cursor:
        # Select the contents of the user's inventory
        cursor.execute("""
            SELECT u.username, g.max_health, g.action_points, g.coins,
                       sw.name, sw.sword_rank, sw.strength_boost, CONCAT('dungeon/sword/', COALESCE(sw.sprite_path, 'default.png')),
                       b.name, b.boots_rank, b.ap_reduction_factor, CONCAT('dungeon/boots/', COALESCE(b.sprite_path, 'default.png')),
                       st.name, st.staff_rank, st.healing_factor, CONCAT('dungeon/staff/', COALESCE(st.sprite_path, 'default.png')),
                       a.name, a.armor_rank, a.defense_factor, CONCAT('dungeon/armor/', COALESCE(a.sprite_path, 'default.png'))
            FROM dungeon_gamestats g JOIN dungeon_sword sw ON g.sword_id = sw.id
                       JOIN dungeon_boots b ON g.boots_id = b.id
                       JOIN dungeon_staff st ON g.staff_id = st.id
                       JOIN dungeon_armor a ON g.armor_id = a.id
                       JOIN gym_fitcrawleruser u ON g.user_id = u.id
            WHERE g.user_id = %s
            """, [id])
        inventory_info = cursor.fetchone()

        sword_path = inventory_info[7]
        boots_path = inventory_info[11]
        staff_path = inventory_info[15]
        armor_path = inventory_info[19]

        sword_info = {
            'name': inventory_info[4], 
            'rank': inventory_info[5], 
            'stats': inventory_info[6], 
            'path': sword_path}
        
        boots_info = {
            'name': inventory_info[8], 
            'rank': inventory_info[9], 
            'stats': inventory_info[10], 
            'path': boots_path}
        
        staff_info = {
            'name': inventory_info[12], 
            'rank': inventory_info[13], 
            'stats': inventory_info[14], 
            'path': staff_path}
        
        armor_info = {
            'name': inventory_info[16], 
            'rank': inventory_info[17], 
            'stats': inventory_info[18], 
            'path': armor_path}
        
        player_inventory['username'] = inventory_info[0]
        player_inventory['max_health'] = inventory_info[1]
        player_inventory['action_points'] = inventory_info[2]
        player_inventory['coins'] = inventory_info[3]

        player_inventory['sword_info'] = sword_info
        player_inventory['boots_info'] = boots_info
        player_inventory['staff_info'] = staff_info
        player_inventory['armor_info'] = armor_info

    return player_inventory


# Helper method to get enemy stats for battles
# - Jason 3/31/25
def get_enemy_stats(battle_id):
    with connection.cursor() as cursor:
        # Fetch the dungeon instance information
            cursor.execute("""
                SELECT e.name, e.strength, e.defense, e.max_health, b.enemy_health
                FROM dungeon_dungeonbattle b JOIN dungeon_dungeonenemy e ON b.enemy_id = e.id
                WHERE b.exploration_id = %s
                """,
                [battle_id]
            )
            enemy_info = cursor.fetchone()
            
            enemy_stats = {}
            enemy_stats['name'] = enemy_info[0]
            enemy_stats['strength'] = enemy_info[1]
            enemy_stats['defense'] = enemy_info[2]
            enemy_stats['health'] = enemy_info[4]
            enemy_stats['max_health'] = enemy_info[3]
            return enemy_stats
            
            
# Helper method for player attack
# - Jason 3/31/25
def battle_player_turn(user_id, user_inventory, enemy_stats, dungeon_layout, current_location):
    results = {}
    
    attack_stength = BASE_DAMAGE_AMOUNT + user_inventory['sword_info']['stats']
    defense_strength = BASE_DEFENSE_AMOUNT + enemy_stats['defense']
    
    damage_amount = max(1, attack_stength - defense_strength)
    results['damage_done'] = damage_amount
    
    
    new_health = enemy_stats['health'] - damage_amount
    
    with connection.cursor() as cursor:
        
        # If the enemy is still alive
        if new_health > 0:
            results['defeat'] = False
            
            # Update the enemy health
            
            cursor.execute("""
                UPDATE dungeon_dungeonbattle
                SET enemy_health = %s
                WHERE exploration_id = %s
                """,
                [new_health,user_id]
            )
            
        # The enemy is defeated, so end the battle instance
        else:
            results['defeat'] = True
            
            cursor.execute("""
                        DELETE FROM dungeon_dungeonbattle
                        WHERE exploration_id = %s
                    """, [user_id])
            
            # Update the layout so that there is no longer an enemy on the current space
            updated_layout = dungeon_layout[:current_location] + '1' + dungeon_layout[current_location+1:] 
            cursor.execute("""
                UPDATE dungeon_dungeonexploration
                SET dungeon_layout = %s
                WHERE user_id = %s
                """,
                [updated_layout,user_id]
            )
            
    
    
    return results

# Helper method for enemy attack
# - Jason 3/31/25
def battle_enemy_turn(user_id, user_inventory, enemy_stats, user_health):
    results = {}
    
    attack_stength = BASE_DAMAGE_AMOUNT + enemy_stats['strength']
    defense_strength = BASE_DEFENSE_AMOUNT + user_inventory['armor_info']['stats']
    
    damage_amount = max(1, attack_stength - defense_strength)
    results['damage_done'] = damage_amount
    
    
    new_health = user_health - damage_amount
    
    
    with connection.cursor() as cursor:
        
        # If the user is still alive
        if new_health > 0:
            results['defeat'] = False
            
            # Update the user health
            
            cursor.execute("""
                UPDATE dungeon_dungeonexploration
                SET health = %s
                WHERE user_id = %s
                """,
                [new_health,user_id]
            )
            
        # The user is defeated, so end the dungeon exploration
        else:
            results['defeat'] = True
            
            # Remove the battle instance
            cursor.execute("""
                    DELETE FROM dungeon_dungeonbattle
                    WHERE exploration_id = %s
                """, [user_id])
            
            # Remove the exploration instance
            cursor.execute("""
                    DELETE FROM dungeon_dungeonexploration
                    WHERE user_id = %s
                """, [user_id])
    
    
    return results

@login_required
def death_screen(request):
    template_args = {}
    template_args['death'] = True
    return render(request, 'dungeon/end_screen.html', template_args)

@login_required
def complete_screen(request):
    template_args = {}
    template_args['complete'] = True
    return render(request, 'dungeon/end_screen.html', template_args)

@login_required
def exit_screen(request):
    template_args = {}
    return render(request, 'dungeon/end_screen.html', template_args)

# End the exploration instance of a dungeon
@login_required
def dungeon_exit(request):
    
    # Ensure the current user is a FitKnight.
    if request.user.user_type != 'FitKnight':
        return redirect('fitness:home')
    
    completed = False
    
    # Ensure that the user is already exploring a dungeon
    if check_for_dungeon_exploration(request.user.id):
        with connection.cursor() as cursor:
        # Fetch the dungeon instance information
            cursor.execute("""
                SELECT e.current_location, e.dungeon_layout
                FROM dungeon_dungeonexploration e
                WHERE e.user_id = %s
                """,
                [request.user.id]
            )
            dungeon_info = cursor.fetchone()

            current_location = dungeon_info[0]
            layout = dungeon_info[1]
            
            # Check if the user has reached the end of the dungeon:
            if layout[current_location] == 'E':
                completed = True
                cursor.execute("""
                    UPDATE dungeon_gamestats
                    SET dungeons_completed = (dungeons_completed + 1)
                    WHERE user_id = %s
                    """,
                    [request.user.id]
                )
                
            # Remove any battle instance
            cursor.execute("""
                    DELETE FROM dungeon_dungeonbattle
                    WHERE exploration_id = %s
                """, [request.user.id])
            
            # Remove the exploration instance
            cursor.execute("""
                    DELETE FROM dungeon_dungeonexploration
                    WHERE user_id = %s
                """, [request.user.id])
            
            
        if completed:
            # Redirect to the complete screen after completing dungeon
            return redirect('dungeon:complete_screen')
        
        else:
            # Redirect to the exit screen after exiting dungeon  
            return redirect('dungeon:exit_screen')
        
    # Otherwise redirect to select screen
    else:
        return redirect('dungeon:dungeon_select')


# Dungeon Select Screen
# - Jason 3/16/25 Started
# - Jason 3/24/25 Completed
@login_required
def dungeon_select(request):
    
    # Ensure the current user is a FitKnight.
    if request.user.user_type != 'FitKnight':
        return redirect('fitness:home')

    # Ensure that the user is not already exploring a dungeon
    if check_for_dungeon_exploration(request.user.id):
        return redirect('dungeon:dungeon_view')

    with connection.cursor() as cursor:
        # Select a list of dungeons for the user to choose from
        cursor.execute("""
            SELECT d.id, d.name, d.description, d.difficulty_score, 
                       CONCAT('dungeon/thumbnails/', COALESCE(d.thumbnail_path, 'default.png'))
            FROM dungeon_dungeon d
            ORDER BY d.difficulty_quantifer, d.name
            """)
        dungeon_info = cursor.fetchall()


    template_args = {'dungeon_info': dungeon_info}

    return render(request, 'dungeon/dungeon_select.html', template_args)

# Helper function that determines the directions that the player can move.
# Returns in terms of forward, backward, left, right.
# Also returns the index of the movable directions, with -1 being unmovable.
# - Jason 3/24/25
def movable_directions(dungeon_layout, dungeon_width, current_position, facing_direction):

    # absolute movable directions
    north = True
    east = True
    west = True
    south = True

    # Output directions
    # f = forwards
    # l = left
    # r = right
    # b = backwards
    output = {}

    if (current_position - dungeon_width) < 0:
        north = False
    elif dungeon_layout[(current_position - dungeon_width)] == '0':
        north = False

    if (current_position + dungeon_width) >= len(dungeon_layout):
        south = False
    elif dungeon_layout[(current_position + dungeon_width)] == '0':
        south = False

    if (current_position % dungeon_width) == 0:
        west = False
    elif dungeon_layout[(current_position - 1)] == '0':
        west = False

    if (current_position % dungeon_width) == (dungeon_width - 1):
        east = False
    elif dungeon_layout[(current_position + 1)] == '0':
        east = False


    if facing_direction == 'N':

        if north:
            output['f'] = current_position - dungeon_width
        else:
            output['f'] = -1 

        if east:
            output['r'] = current_position + 1
        else:
            output['r'] = -1 

        if west:
            output['l'] = current_position - 1
        else:
            output['l'] = -1 

        if south:
            output['b'] = current_position + dungeon_width
        else:
            output['b'] = -1 

    elif facing_direction == 'E':

        if north:
            output['l'] = current_position - dungeon_width
        else:
            output['l'] = -1 

        if east:
            output['f'] = current_position + 1
        else:
            output['f'] = -1 

        if west:
            output['b'] = current_position - 1
        else:
            output['b'] = -1 

        if south:
            output['r'] = current_position + dungeon_width
        else:
            output['r'] = -1 

    elif facing_direction == 'W':

        if north:
            output['r'] = current_position - dungeon_width
        else:
            output['r'] = -1 

        if east:
            output['b'] = current_position + 1
        else:
            output['b'] = -1 

        if west:
            output['f'] = current_position - 1
        else:
            output['f'] = -1 

        if south:
            output['l'] = current_position + dungeon_width
        else:
            output['l'] = -1 

    # Else, facing south
    else:

        if north:
            output['b'] = current_position - dungeon_width
        else:
            output['b'] = -1 

        if east:
            output['l'] = current_position + 1
        else:
            output['l'] = -1 

        if west:
            output['r'] = current_position - 1
        else:
            output['r'] = -1 

        if south:
            output['f'] = current_position + dungeon_width
        else:
            output['f'] = -1 

    return output


# Returns a string represented an initialized dungeon instance.
# Helper function for dungeon_begin_exploration.
# - Jason 3/24/25
def generate_dungeon(dungeon_schematic, wall_spawn, chest_spawn, common_spawn, uncommon_spawn, boss_spawn):
    layout = dungeon_schematic

    for i in range(len(layout)):

        # conditional chest
        if layout[i] == 'c':
            if random.random() < chest_spawn:
                layout = layout[:i] + 'C' + layout[i+1:]
            else:
                layout = layout[:i] + '1' + layout[i+1:]

        # conditional wall
        elif layout[i] == 'o':
            if random.random() < wall_spawn:
                layout = layout[:i] + '0' + layout[i+1:]
            else:
                layout = layout[:i] + '1' + layout[i+1:]

        # conditional common monster
        elif layout[i] == 'x':
            if random.random() < common_spawn:
                layout = layout[:i] + 'X' + layout[i+1:]
            else:
                layout = layout[:i] + '1' + layout[i+1:]

        # conditional uncommon monster
        elif layout[i] == 'y':
            if random.random() < uncommon_spawn:
                layout = layout[:i] + 'Y' + layout[i+1:]
            else:
                layout = layout[:i] + '1' + layout[i+1:]

        # conditional boss monster
        elif layout[i] == 'z':
            if random.random() < boss_spawn:
                layout = layout[:i] + 'Z' + layout[i+1:]
            else:
                layout = layout[:i] + '1' + layout[i+1:]

    return layout


# Helper function to determine whether the user is already exploring a dungeon.
# Returns True if the user is exploring a dungeon, otherwise returns false
# - Jason 3/24/25
def check_for_dungeon_exploration(user_id):
    with connection.cursor() as cursor:
        # Check if the user already has a dungeon exploration
        cursor.execute("""
            SELECT dungeon_id, user_id
            FROM dungeon_dungeonexploration
            WHERE user_id = %s
            """,
            [user_id]
        )

        return (cursor.fetchone() is not None)
    

# Helper function to determine whether the user is in a battle.
# Returns True if the user is in a battle, otherwise returns false
# - Jason 3/31/25
def check_for_dungeon_battle(user_id):
    with connection.cursor() as cursor:
        # Check if the user already has a dungeon exploration
        cursor.execute("""
            SELECT exploration_id, enemy_id
            FROM dungeon_dungeonbattle
            WHERE exploration_id = %s
            """,
            [user_id]
        )

        return (cursor.fetchone() is not None)


@login_required
def heal(request):
    # Ensure the current user is a FitKnight.
    if request.user.user_type != 'FitKnight':
        return redirect('fitness:home')
    
    # Ensure that the user is already exploring a dungeon
    if check_for_dungeon_exploration(request.user.id):
        
        inventory = get_player_inventory(request.user.id)
        
        max_health = inventory['max_health']
        
        # Calculate the healing cost (formula subject to change)
        heal_cost = HEAL_BASE_COST
        heal_amount = BASE_HEAL_AMOUNT * inventory['staff_info']['stats']
        
        # Determine whether the player is in battle
        in_battle = check_for_dungeon_battle(request.user.id)
        
        
        # If the user has enough action points to heal:
        if inventory['action_points'] >= heal_cost:
            
            with connection.cursor() as cursor:
                cursor.execute("""
                               SELECT user_id, health
                               FROM dungeon_dungeonexploration
                               WHERE user_id = %s
                               """,
                               [request.user.id]
                               )
                
                current_health = cursor.fetchone()[1]
                
                # Deduct action points
                cursor.execute("""
                    UPDATE dungeon_gamestats
                    SET action_points = (action_points - %s)
                    WHERE user_id = %s
                    """,
                    [heal_cost, request.user.id]
                )
                new_health = min(max_health, heal_amount + current_health)
                # Heal health
                cursor.execute("""
                    UPDATE dungeon_dungeonexploration
                    SET health = %s
                    WHERE user_id = %s
                    """,
                    [new_health, request.user.id]
                )
                
                # If the user is in a battle, the enemy takes a turn afterward
                if in_battle:
                    enemy_stats = get_enemy_stats(request.user.id)
                    
                    # Then, the enemy attacks
                    enemy_results = battle_enemy_turn(request.user.id, inventory, enemy_stats, new_health)
                    # If the player is defeated
                    if enemy_results['defeat']:
                        return redirect('dungeon:death_screen')
                    
                    return redirect(reverse('dungeon:dungeon_battle') + '?' + urlencode({'player_heal':heal_amount}) + '&' + urlencode({'enemy_damage':enemy_results['damage_done']}) + '&' + urlencode({'enemy_type':enemy_stats['name']} ))
                
                else:
                    return redirect('dungeon:dungeon_view')
            
        # Otherwise they are too exhausted to heal
        else:
            if in_battle:
                return redirect(reverse('dungeon:dungeon_battle') + '?' + urlencode({'exhausted':True}))   
            else:
                return redirect(reverse('dungeon:dungeon_view') + '?' + urlencode({'exhausted':True}))   
                
    # Otherwise send them to the dungeon select screen
    else:
        return redirect('dungeon:dungeon_select')
    


# Initializes a dungeon exploration instance for the user.
# - Jason 3/16/25 Started
# - Jason 3/24/25 Finished
@login_required
def dungeon_begin_exploration(request, dungeon_pk):
    # Ensure the current user is a FitKnight.
    if request.user.user_type != 'FitKnight':
        return redirect('fitness:home')
    
    # Ensure that the user has gamestats
    check_and_create_game_stats(request.user.id)

    # Ensure that the user is not already exploring a dungeon
    if check_for_dungeon_exploration(request.user.id):
        return redirect('dungeon:dungeon_view')

    with connection.cursor() as cursor:

        # Fetch the dungeon's schematics to make an instance of the dungeon
        cursor.execute("""
            SELECT layout, wall_spawn, chest_spawn, common_monster_spawn, uncommon_monster_spawn, boss_monster_spawn
            FROM dungeon_dungeon
            WHERE id = %s
            """,
            [dungeon_pk]
        )
        dungeon_schem = cursor.fetchone()

        layout = generate_dungeon(dungeon_schem[0], dungeon_schem[1], dungeon_schem[2], dungeon_schem[3], dungeon_schem[4], dungeon_schem[5])
        start_location = layout.index('S')

        # Determine the user's maximum health for initialization
        cursor.execute("""
            SELECT user_id, max_health
            FROM dungeon_gamestats
            WHERE user_id = %s
            """,
            [request.user.id]
        )
        initial_health = cursor.fetchone()[1]

        cursor.execute("""
            INSERT INTO dungeon_dungeonexploration
            (user_id, current_location, previous_location, direction, health, exploration_start, dungeon_id, dungeon_layout)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            [request.user.id, start_location, start_location, 'N', initial_health, datetime.datetime.now(), dungeon_pk, layout]
        )
        # Direction can be 'N' (North), 'E' (East), 'W' (West), 'S' (South). Starts as North.
   
    return redirect('dungeon:dungeon_view')

@login_required
def dungeon_battle_view(request):
    # Ensure the current user is a FitKnight.
    if request.user.user_type != 'FitKnight':
        return redirect('fitness:home')
    
    # Ensure that the user is already in a battle,
    # if they aren't then redirect them to the dungeon view
    if not check_for_dungeon_battle(request.user.id):
        return redirect('dungeon:dungeon_view')
    
    
    template_args = {}
    
    # Flag to display message if the user's action fails due to exhaustion
    if request.GET.get('exhausted'):
        template_args['status'] = 'You are too exhausted to do that.'
        
    if request.GET.get('player_damage'):
        template_args['status'] = '\nYou did ' + request.GET.get('player_damage') + ' damage.\n' + request.GET.get('enemy_type') + ' did ' + request.GET.get('enemy_damage') + ' damage.'
    
    
    if request.GET.get('player_heal'):
        template_args['status'] = '\nYou healed ' + request.GET.get('player_heal') + ' health.\n' + request.GET.get('enemy_type') + ' did ' + request.GET.get('enemy_damage') + ' damage.'
    
    with connection.cursor() as cursor:
        # Fetch the dungeon instance information
        cursor.execute("""
            SELECT e.current_location, e.dungeon_layout, e.direction, d.width, d.sprite_folder, 
                       d.common_monster_id, d.uncommon_monster_id, d.boss_monster_id, e.health
            FROM dungeon_dungeonexploration e JOIN dungeon_dungeon d ON e.dungeon_id = d.id
            WHERE e.user_id = %s
            """,
            [request.user.id]
        )
        dungeon_info = cursor.fetchone()

        current_location = dungeon_info[0]
        direction = dungeon_info[2]
        layout = dungeon_info[1]

        inventory = get_player_inventory(request.user.id)
        template_args['inventory'] = inventory
        template_args['health'] = dungeon_info[8]
        
        template_args['movement_cost'] = MOVEMENT_AP_BASE_COST * inventory['boots_info']['stats']
        template_args['heal_cost'] = HEAL_BASE_COST 
        template_args['heal_amount'] = BASE_HEAL_AMOUNT * inventory['staff_info']['stats']
        
        template_args['attack_cost'] = ATTACK_AP_BASE_COST
        template_args['escape_cost'] = ESCAPE_AP_BASE_COST

        movable = movable_directions(layout, dungeon_info[3], current_location, direction)

        wall_string = 'W'

        if movable['l'] > -1:
            wall_string = wall_string + 'l'
            template_args['left'] = True
        
        if movable['f'] > -1:
            wall_string = wall_string + 'f'
            template_args['forwards'] = True

        if movable['r'] > -1:
            wall_string = wall_string + 'r'
            template_args['right'] = True

        if movable['b'] > -1:
            template_args['backwards'] = True

        wall_string = wall_string + '.png'

        dungeon_sprite_path = 'dungeon/dungeon_sprites/default/'
        if dungeon_info[4]:
            dungeon_sprite_path = 'dungeon/dungeon_sprites/' + dungeon_info[4] + '/'

        template_args['background'] = dungeon_sprite_path + wall_string
        
        if direction == 'N':
            template_args['north'] = True
        elif direction == 'E':
            template_args['east'] = True
        elif direction == 'W':
            template_args['west'] = True
        # Otherwise, south
        else:
            template_args['south'] = True

        
        cursor.execute("""
            SELECT e.name, CONCAT('dungeon/enemies/', COALESCE(e.sprite_path, 'default.png')), b.enemy_health, e.max_health
            FROM dungeon_dungeonbattle b JOIN dungeon_dungeonenemy e ON b.enemy_id = e.id
            WHERE b.exploration_id = %s
            """,
            [request.user.id]
            )
        monster_info = cursor.fetchone()
        template_args['monster'] = monster_info[1]
        template_args['monster_name'] = monster_info[0]
        template_args['monster_max_health'] =  monster_info[3]
        template_args['monster_health'] =  monster_info[2]
     

    return render(request, 'dungeon/battle_view.html', template_args)

@login_required
def battle_attack(request):
    
    # Ensure the current user is a FitKnight.
    if request.user.user_type != 'FitKnight':
        return redirect('fitness:home')
    
    # Ensure that the user is in a battle,
    # if they aren't, then redirect them to the dungeon view screen.
    if not check_for_dungeon_battle(request.user.id):
        return redirect('dungeon:dungeon_view')
    
    inventory = get_player_inventory(request.user.id)
    enemy_stats = get_enemy_stats(request.user.id)
    
    # Ensure the user has enough AP to attack
    new_AP = inventory['action_points'] - ATTACK_AP_BASE_COST
    
    if new_AP < 0:
        return redirect(reverse('dungeon:dungeon_battle') + '?' + urlencode({'exhausted':True}))   
    

    
    with connection.cursor() as cursor:
        # Fetch the dungeon instance information
        cursor.execute("""
            SELECT e.current_location, e.dungeon_layout, e.health, d.difficulty_quantifer
            FROM dungeon_dungeonexploration e JOIN dungeon_dungeon d ON e.dungeon_id = d.id
            WHERE e.user_id = %s
            """,
            [request.user.id]
        )
        dungeon_info = cursor.fetchone()
        user_health = dungeon_info[2]
        layout = dungeon_info[1]
        location = dungeon_info[0]
        difficulty_level = math.ceil(dungeon_info[3])
        
        enemy_type = layout[location]
        
        # Update the player's action points
        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE dungeon_gamestats
                SET action_points = %s
                WHERE user_id = %s
                """, [new_AP,request.user.id])
        
        # First, the user attacks
        player_results = battle_player_turn(request.user.id, inventory, enemy_stats, layout, location)
        
        # If the enemy is defeated
        if player_results['defeat']:
            rewarded = battle_reward(request.user.id, enemy_type, difficulty_level)
            
            return redirect(reverse('dungeon:dungeon_view') + '?' + urlencode({'battle_earn':rewarded}))  
        
        
        # Then, the enemy attacks
        enemy_results = battle_enemy_turn(request.user.id, inventory, enemy_stats, user_health)
        
        # If the player is defeated
        if enemy_results['defeat']:
            return redirect('dungeon:death_screen')
        

    return redirect(reverse('dungeon:dungeon_battle') + '?' + urlencode({'player_damage':player_results['damage_done']}) + '&' + urlencode({'enemy_damage':enemy_results['damage_done']}) + '&' + urlencode({'enemy_type':enemy_stats['name']} ))  
        
        
# User opens a chest and receives its rewards
# - Jason 3/31/25
@login_required
def open_chest(request):
    
    # Ensure the current user is a FitKnight.
    if request.user.user_type != 'FitKnight':
        return redirect('fitness:home')
    
    # Ensure that the user is already exploring a dungeon,
    # if they aren't, then redirect them to the select screen
    if not check_for_dungeon_exploration(request.user.id):
        return redirect('dungeon:dungeon_select')
    
    
    with connection.cursor() as cursor:
        # Fetch the dungeon instance information
        cursor.execute("""
            SELECT e.current_location, e.dungeon_layout, d.difficulty_quantifer
            FROM dungeon_dungeonexploration e JOIN dungeon_dungeon d ON e.dungeon_id = d.id
            WHERE e.user_id = %s
            """,
            [request.user.id]
        )
        dungeon_info = cursor.fetchone()
        current_location = dungeon_info[0]
        current_layout = dungeon_info[1]
        difficulty = math.ceil(dungeon_info[2])
        
        
        
        # If the user is standing on a chest

        if current_layout[current_location] == 'C':
            new_layout = current_layout[:current_location] + '1' + current_layout[current_location+1:] 
            
            # Reward the player
            rewarded = chest_reward(request.user.id, difficulty)
            
            # Remove the chest
            cursor.execute("""
                UPDATE dungeon_dungeonexploration
                SET dungeon_layout = %s
                WHERE user_id = %s
                """, [new_layout, request.user.id])
            
            return redirect(reverse('dungeon:dungeon_view') + '?' + urlencode({'chest_earn':rewarded}))  
        

    # Otherwise the user isn't on a chest, so redirect them to the dungeon view
    
    return redirect('dungeon:dungeon_view')
            
    

# Lets the user escape from a battle at the cost of AP
# - Jason 3/31/25
@login_required
def battle_retreat(request):
    # Ensure the current user is a FitKnight.
    if request.user.user_type != 'FitKnight':
        return redirect('fitness:home')
    
    # Ensure that the user is in a battle,
    # if they aren't, then redirect them to the dungeon view.
    if not check_for_dungeon_battle(request.user.id):
        return redirect('dungeon:dungeon_view')
    
    inventory = get_player_inventory(request.user.id)
    
    # Ensure the user has enough AP to flee
    new_AP = inventory['action_points'] - ESCAPE_AP_BASE_COST
    
    if new_AP < 0:
        return redirect(reverse('dungeon:dungeon_battle') + '?' + urlencode({'exhausted':True}))   
    
    
    # Update the player's action points
    with connection.cursor() as cursor:
        cursor.execute("""
            UPDATE dungeon_gamestats
            SET action_points = %s
            WHERE user_id = %s
            """, [new_AP,request.user.id])
        
        # Move the user out of the battle
        cursor.execute("""
            SELECT current_location, previous_location 
            FROM dungeon_dungeonexploration
            WHERE user_id = %s
            """, [request.user.id])
        
        prev_location = cursor.fetchone()[1]
        
        # Move the user out of the battle
        cursor.execute("""
            UPDATE dungeon_dungeonexploration
            SET current_location = %s
            WHERE user_id = %s
            """, [prev_location, request.user.id])
        
        # Delete the battle instance
        cursor.execute("""
                        DELETE FROM dungeon_dungeonbattle
                        WHERE exploration_id = %s
                    """, [request.user.id])
        
        
    
    return redirect('dungeon:dungeon_view')
        
    


# Display the current room of the dungeon
# - Jason 3/24/25
@login_required
def dungeon_view(request):
    
    # Ensure the current user is a FitKnight.
    if request.user.user_type != 'FitKnight':
        return redirect('fitness:home')

    # Ensure that the user is already exploring a dungeon,
    # if they aren't, then redirect them to the select screen
    if not check_for_dungeon_exploration(request.user.id):
        return redirect('dungeon:dungeon_select')
    
    # Ensure that the user is not already in a battle,
    # if they are, then redirect them to the battle screen.
    if check_for_dungeon_battle(request.user.id):
        return redirect('dungeon:dungeon_battle')
    
    
    
    template_args = {}
    
    # Flag to display message if the user's movement fails due to exhaustion
    if request.GET.get('exhausted'):
        template_args['status'] = 'You are too exhausted to move.'
        
    if request.GET.get('chest_earn'):
        template_args['status'] = 'You found ' + request.GET.get('chest_earn') + ' coins in the chest.'
        
    if request.GET.get('battle_earn'):
        template_args['status'] = 'You found ' + request.GET.get('battle_earn') + ' coins after the battle.'
    
    with connection.cursor() as cursor:
        # Fetch the dungeon instance information
        cursor.execute("""
            SELECT e.current_location, e.dungeon_layout, e.direction, d.width, d.sprite_folder, 
                       d.common_monster_id, d.uncommon_monster_id, d.boss_monster_id, e.health
            FROM dungeon_dungeonexploration e JOIN dungeon_dungeon d ON e.dungeon_id = d.id
            WHERE e.user_id = %s
            """,
            [request.user.id]
        )
        dungeon_info = cursor.fetchone()

        current_location = dungeon_info[0]
        direction = dungeon_info[2]
        layout = dungeon_info[1]

        inventory = get_player_inventory(request.user.id)
        template_args['inventory'] = inventory
        template_args['health'] = dungeon_info[8]
        
        template_args['movement_cost'] = MOVEMENT_AP_BASE_COST * inventory['boots_info']['stats']
        template_args['heal_cost'] = HEAL_BASE_COST 
        template_args['heal_amount'] = BASE_HEAL_AMOUNT * inventory['staff_info']['stats']

        movable = movable_directions(layout, dungeon_info[3], current_location, direction)

        wall_string = 'W'

        if movable['l'] > -1:
            wall_string = wall_string + 'l'
            template_args['left'] = True
        
        if movable['f'] > -1:
            wall_string = wall_string + 'f'
            template_args['forwards'] = True

        if movable['r'] > -1:
            wall_string = wall_string + 'r'
            template_args['right'] = True

        if movable['b'] > -1:
            template_args['backwards'] = True

        wall_string = wall_string + '.png'

        dungeon_sprite_path = 'dungeon/dungeon_sprites/default/'
        if dungeon_info[4]:
            dungeon_sprite_path = 'dungeon/dungeon_sprites/' + dungeon_info[4] + '/'

        template_args['background'] = dungeon_sprite_path + wall_string
        
        if direction == 'N':
            template_args['north'] = True
        elif direction == 'E':
            template_args['east'] = True
        elif direction == 'W':
            template_args['west'] = True
        # Otherwise, south
        else:
            template_args['south'] = True

        # Check if the user is standing on a chest
        if layout[current_location] == 'C':
            print("chest debug")
            template_args['chest'] = dungeon_sprite_path + 'chest' + direction + '.png'

        # Check if the user is standing on the exit
        if layout[current_location] == 'E':
            template_args['portal'] = dungeon_sprite_path + 'portal.png'

        monster = -1
        # Check if the user is standing on a common monster
        if layout[current_location] == 'X':
            monster = dungeon_info[5]

        # Check if the user is standing on an uncommon monster
        if layout[current_location] == 'Y':
            monster = dungeon_info[6]

        # Check if the user is standing on a boss monster
        if layout[current_location] == 'Z':
            monster = dungeon_info[7]

        # Get the monster info
        if monster > -1:
            cursor.execute("""
            SELECT name, max_health
            FROM dungeon_dungeonenemy
            WHERE id = %s
            """,
            [monster]
            )
            monster_health = cursor.fetchone()[1]
            
            # Create a battle instance
            cursor.execute("""
                    INSERT INTO dungeon_dungeonbattle
                    (exploration_id, enemy_id, enemy_health)
                    VALUES (%s, %s, %s)
                    """,
                    [request.user.id, monster, monster_health]
                    )
            
            return redirect('dungeon:dungeon_battle')
     

    return render(request, 'dungeon/view_dungeon.html', template_args)

# Move through the dungeon
# - Jason 3/24/25 Started
# - Jason (forget the date) Finished
@login_required
def dungeon_traverse(request, direction):
    # Ensure the current user is a FitKnight.
    if request.user.user_type != 'FitKnight':
        return redirect('fitness:home')
    
    # Ensure that the user is not already in a battle,
    # if they are, then redirect them to the battle screen.
    if check_for_dungeon_battle(request.user.id):
        return redirect('dungeon:dungeon_battle')
    
    # Determine whether the user has enough action points to move
    inventory = get_player_inventory(request.user.id)
    
    movement_cost = MOVEMENT_AP_BASE_COST * inventory['boots_info']['stats']
    new_AP = inventory['action_points'] - movement_cost
    
    if new_AP < 0:
        return redirect(reverse('dungeon:dungeon_view') + '?' + urlencode({'exhausted':True}))        
    
    with connection.cursor() as cursor:
        
        # Fetch the direction the user is currently facing
        cursor.execute("""
            SELECT e.current_location, e.direction, e.dungeon_layout, d.width
            FROM dungeon_dungeonexploration e JOIN dungeon_dungeon d ON e.dungeon_id = d.id
            WHERE e.user_id = %s
            """,
            [request.user.id]
            )
        
        previous_location, facing_direction, dungeon_layout, dungeon_width = cursor.fetchone()
        
        # Initialize new location as the previous location in case something goes wrong
        new_location = previous_location
        
        moves = movable_directions(dungeon_layout, dungeon_width, previous_location, facing_direction)
        
        if direction == 'forwards':
            # Movement is valid
            if moves['f'] > -1:
                new_location = moves['f']
            # Movement fails
            else:
                return redirect('dungeon:dungeon_view')
            
        elif direction == 'left':
            # Movement is valid
            if moves['l'] > -1:
                new_location = moves['l']
            # Movement fails
            else:
                return redirect('dungeon:dungeon_view')
            
        elif direction == 'right':
            # Movement is valid
            if moves['r'] > -1:
                new_location = moves['r']
            # Movement fails
            else:
                return redirect('dungeon:dungeon_view')
            
        # otherwise the direction is backwards
        else:
            # Movement is valid
            if moves['b'] > -1:
                new_location = moves['b']
            # Movement fails
            else:
                return redirect('dungeon:dungeon_view')
            
            
        # update the position in the dungeon
        cursor.execute("""
                    UPDATE dungeon_dungeonexploration
                    SET current_location = %s, previous_location = %s
                    WHERE user_id = %s
                    """,
                    [new_location, previous_location, request.user.id]
                    )
        
        # deduct the movement AP cost
        cursor.execute("""
                    UPDATE dungeon_gamestats
                    SET action_points = %s
                    WHERE user_id = %s
                    """,
                    [new_AP, request.user.id]
                    )
        
    # Display the new position in the dungeon 
    return redirect('dungeon:dungeon_view')

# Change directions in the dungeon
# - Jason 3/24/25 Started. 
# - Jason (forget the date) Finished
@login_required
def dungeon_rotate(request, direction):
    
    # Ensure the current user is a FitKnight.
    if request.user.user_type != 'FitKnight':
        return redirect('fitness:home')
    
    with connection.cursor() as cursor:
        # Fetch the direction the user is currently facing
        cursor.execute("""
            SELECT current_location, direction
            FROM dungeon_dungeonexploration
            WHERE user_id = %s
            """,
            [request.user.id]
            )
        
        # Default new direction to North in case of errors
        new_direction = 'N'
        
        current_direction = cursor.fetchone()[1]
        # Current direction is north
        if current_direction == 'N':
            # If turn left
            if direction == 'left':
               new_direction = 'W'
            # Else turn right
            else:
                new_direction = 'E'
                
        # Current direction is east 
        elif current_direction == 'E':
            # If turn left
            if direction == 'left':
               new_direction = 'N'
            # Else turn right
            else:
                new_direction = 'S'
                
        # Current direction is west 
        elif current_direction == 'W':
            # If turn left
            if direction == 'left':
               new_direction = 'S'
            # Else turn right
            else:
                new_direction = 'N'
                
        # Current direction is south
        else:
            # If turn left
            if direction == 'left':
               new_direction = 'E'
            # Else turn right
            else:
                new_direction = 'W'
        
        # update the current direction
        cursor.execute("""
                    UPDATE dungeon_dungeonexploration
                    SET direction = %s
                    WHERE user_id = %s
                    """,
                    [new_direction, request.user.id]
                    )
    
    return redirect('dungeon:dungeon_view')

# This view allows for the user to view their inventory contents
# - Jason 3/16/25
@login_required
def view_inventory(request):
    # Ensure the current user is a FitKnight.
    if request.user.user_type != 'FitKnight':
        return redirect('fitness:home')
    
    # Ensure that the user has gamestats
    check_and_create_game_stats(request.user.id)

    inventory = get_player_inventory(request.user.id)

    return render(request, 'dungeon/view_inventory.html', inventory)

# This function allows for the user to view the milestones and rewards.
# - Jason 3/8/25, Updated Jason 3/16/25
@login_required
def view_milestones(request):
    # Ensure the current user is a FitKnight.
    if request.user.user_type != 'FitKnight':
        return redirect('fitness:home')
    
    # Ensure that the user has gamestats
    check_and_create_game_stats(request.user.id)

    with connection.cursor() as cursor:
        # Determine the total number of each difficulty task the user has completed
        tasks_completed = []
        for difficulty in ['Noob', 'Easy', 'Medium', 'Hard', 'Expert']:
            cursor.execute("""
                SELECT COUNT(*)
                FROM fitness_task t JOIN fitness_tasklog tl ON t.id = tl.task_id
                WHERE t.user_id = %s
                AND t.difficulty_score = %s
                AND tl.percent_completion >= %s
                """,
                [request.user.id, difficulty, TASK_COMPLETION_REQUIREMENT]
            )
            tasks_completed.append(cursor.fetchone()[0])

        # Determine the user's total daily progress
        cursor.execute("""
            SELECT SUM(minutes_walked), SUM(water_drank_L), SUM(fruit_veggie_servings)
            FROM fitness_dailylog
            WHERE user_id = %s
            """,
            [request.user.id]
        )
        daily_totals = cursor.fetchone()

        # Determine the number of dungeons that the user has completed
        cursor.execute("""
            SELECT dungeons_completed
            FROM dungeon_gamestats
            WHERE user_id = %s
            """,
            [request.user.id]
        )
        total_dungeons = cursor.fetchone()[0]

        # Select the milestones that the user has not completed yet

        cursor.execute("""
            SELECT m.id, m.num_noob_task, m.num_easy_task, m.num_medium_task, m.num_hard_task, m.num_expert_task,
                    m.total_minutes_walked, m.total_water_drank_L, m.total_fruit_veggie_servings, 
                    m.total_dungeons_completed, m.reward_action_points, m.reward_max_health,
                    sw.name, sw.sword_rank, b.name, b.boots_rank, st.name, st.staff_rank, a.name, a.armor_rank
                       
            FROM dungeon_milestone m LEFT JOIN dungeon_sword sw ON m.reward_sword_id = sw.id
                       LEFT JOIN dungeon_boots b ON m.reward_boots_id = b.id
                       LEFT JOIN dungeon_staff st ON m.reward_staff_id = st.id
                       LEFT JOIN dungeon_armor a ON m.reward_armor_id = a.id
            WHERE m.id NOT IN (
                       SELECT milestone_id 
                       FROM dungeon_milestonelog ml
                       WHERE user_id = %s
                       )
            """,
            [request.user.id]
        )
        milestone_info = cursor.fetchall()
    
    template_args = {
        'noob_tasks': tasks_completed[0], 
        'easy_tasks': tasks_completed[1], 
        'medium_tasks': tasks_completed[2], 
        'hard_tasks': tasks_completed[3], 
        'expert_tasks': tasks_completed[4],
        'total_walk': daily_totals[0],
        'total_water': daily_totals[1],
        'total_fruit_veg': daily_totals[2],
        'total_dungeons': total_dungeons,
        'milestone_info': milestone_info}
            
    return render(request, 'dungeon/view_milestones.html', template_args)

# This function allows for the user to complete a milestone and claim its rewards.
# This feature does not require a separate view. This function is accessed from hyperlinks on
# the view_milestones function's page. After updating the database, the user is redirected to the 
# view_milestones page.

# - Jason 3/8/25

@login_required
def complete_milestone(request, milestone_pk):
    # Ensure the current user is a FitKnight.
    if request.user.user_type != 'FitKnight':
        return redirect('fitness:home')
    
    # Ensure that the user has gamestats
    check_and_create_game_stats(request.user.id)

    # Check whether this user has claimed this milestone before
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT *
            FROM dungeon_milestonelog
            WHERE user_id = %s AND milestone_id = %s
            """,
            [request.user.id, milestone_pk]
        )
        existing_milestonelog = cursor.fetchone()

        # If the user already has claimed this milestone before, do not let them do it again.
        # Instead, redirect them to the view milestones page.
        if existing_milestonelog:
            return redirect('dungeon:view_milestones')
        
        # Otherwise, check if the user has actually completed the milestone
        else:

            # Determine the total number of each difficulty task the user has completed
            tasks_completed = []
            for difficulty in ['Noob', 'Easy', 'Medium', 'Hard', 'Expert']:
                cursor.execute("""
                    SELECT COUNT(*)
                    FROM fitness_task t JOIN fitness_tasklog tl ON t.id = tl.task_id
                    WHERE t.user_id = %s
                    AND t.difficulty_score = %s
                    AND tl.percent_completion >= %s
                    """,
                    [request.user.id, difficulty, TASK_COMPLETION_REQUIREMENT]
                )
                tasks_completed.append(cursor.fetchone()[0])

            # Determine the user's total daily progress
            cursor.execute("""
                SELECT SUM(minutes_walked), SUM(water_drank_L), SUM(fruit_veggie_servings)
                FROM fitness_dailylog
                WHERE user_id = %s
                """,
                [request.user.id]
            )
            daily_totals = cursor.fetchone()

            # Get the milestone requirements (and reward information)
            cursor.execute("""
                SELECT num_noob_task, num_easy_task, num_medium_task, num_hard_task, num_expert_task,
                       total_minutes_walked, total_water_drank_L, total_fruit_veggie_servings, total_dungeons_completed,
                       reward_action_points, reward_sword_id, reward_boots_id, reward_staff_id, reward_armor_id, reward_max_health
                FROM dungeon_milestone
                WHERE id = %s
                """,
                [milestone_pk]
            )
            milestone_info = cursor.fetchone()

            # Get the user's current actions points, gear information, and dungeon completion status
            cursor.execute("""
                SELECT g.action_points, g.sword_id, sw.sword_rank, g.boots_id, b.boots_rank, 
                            g.staff_id, st.staff_rank, g.armor_id, a.armor_rank, g.max_health, g.dungeons_completed
                FROM dungeon_gamestats g JOIN dungeon_sword sw ON g.sword_id = sw.id
                            JOIN dungeon_staff st ON g.staff_id = st.id
                            JOIN dungeon_boots b ON g.boots_id = b.id
                            JOIN dungeon_armor a ON g.armor_id = a.id
                WHERE user_id = %s
            """,
            [request.user.id]
            )
            user_current_stats = cursor.fetchone()

            # If the user successfully completed the milestone conditions
            if (milestone_info[0] <= tasks_completed[0] and
                milestone_info[1] <= tasks_completed[1] and
                milestone_info[2] <= tasks_completed[2] and
                milestone_info[3] <= tasks_completed[3] and
                milestone_info[4] <= tasks_completed[4] and
                milestone_info[5] <= daily_totals[0] and
                milestone_info[6] <= daily_totals[1] and
                milestone_info[7] <= daily_totals[2] and
                milestone_info[8] <= user_current_stats[10]):
                

                # If the milestone rewards a sword
                if milestone_info[10]:
                    cursor.execute("""
                        SELECT id, sword_rank
                        FROM dungeon_sword
                        WHERE id = %s
                    """,
                    [milestone_info[10]]
                    )
                    reward_sword_info = cursor.fetchone()
                    # Only if the reward sword's rank is higher, replace the old sword.
                    if reward_sword_info[1] > user_current_stats[2]:
                        new_sword = reward_sword_info[0]
                    # Otherwise keep the old sword
                    else:
                        new_sword = user_current_stats[1]

                else:
                    new_sword = user_current_stats[1]

                # If the milestone rewards boots
                if milestone_info[11]:
                    cursor.execute("""
                        SELECT id, boots_rank
                        FROM dungeon_boots 
                        WHERE id = %s
                    """,
                    [milestone_info[11]]
                    )
                    reward_boots_info = cursor.fetchone()
                    # Only if the reward boots' rank is higher, replace the old boots.
                    if reward_boots_info[1] > user_current_stats[4]:
                        new_boots = reward_boots_info[0]
                    # Otherwise keep the old boots
                    else:
                        new_boots = user_current_stats[3]

                else:
                    new_boots = user_current_stats[3]

                # If the milestone rewards a staff
                if milestone_info[12]:
                    cursor.execute("""
                        SELECT id, staff_rank
                        FROM dungeon_staff
                        WHERE id = %s
                    """,
                    [milestone_info[12]]
                    )
                    reward_staff_info = cursor.fetchone()
                    # Only if the reward staff's rank is higher, replace the old staff.
                    if reward_staff_info[1] > user_current_stats[6]:
                        new_staff = reward_staff_info[0]
                    # Otherwise keep the old staff
                    else:
                        new_staff = user_current_stats[5]

                else:
                    new_staff = user_current_stats[5]

                # If the milestone rewards armor
                if milestone_info[13]:
                    cursor.execute("""
                        SELECT id, armor_rank
                        FROM dungeon_armor
                        WHERE id = %s
                    """,
                    [milestone_info[13]]
                    )
                    reward_armor_info = cursor.fetchone()
                    # Only if the reward armor's rank is higher, replace the old armor.
                    if reward_armor_info[1] > user_current_stats[8]:
                        new_armor = reward_armor_info[0]
                    # Otherwise keep the old armor
                    else:
                        new_armor = user_current_stats[7]

                else:
                    new_armor = user_current_stats[7]

                new_action_points = user_current_stats[0] + milestone_info[9]
                new_max_health = user_current_stats[9] + milestone_info[14]

                # Now update the user's gamestats after applying the milestone's rewards
                cursor.execute("""
                    UPDATE dungeon_gamestats
                    SET action_points = %s, sword_id = %s, boots_id = %s, staff_id = %s, armor_id = %s, max_health = %s
                    WHERE user_id = %s
                    """,
                    [new_action_points, new_sword, new_boots, new_staff, new_armor, new_max_health, request.user.id]
                    )
                

                # Log the completion of the milestone so that the user cannot claim its rewards again
                cursor.execute("""
                    INSERT INTO dungeon_milestonelog
                    (user_id, milestone_id, time_completed)
                    VALUES (%s, %s, %s)
                    """,
                    [request.user.id, milestone_pk, datetime.datetime.now()]
                    )
                
                # Finally, return the user to the view milestones page
                return redirect('dungeon:view_milestones')

            else:
                # Otherwise the user did not complete the milestone's conditions yet, so nothing is done
                return redirect('dungeon:view_milestones')