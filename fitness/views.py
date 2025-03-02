from math import ceil
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, connection

import datetime

# Create your views here.

NUM_ENTRIES_PER_PAGE = 10

# Amount of daily progress in order to earn the daily reward
DAILY_WATER = 1.5
DAILY_FRUIT_VEG = 3
DAILY_WALK = 30

# Amount of action points to reward each daily quest
DAILY_REWARD = 5

def redirect_home(request):
    return redirect('fitness:home')

def home(request):
    return render(request, 'fitness/home.html')

# Helper function for getting the default gear ids
def get_beginner_gear_ids():
    with connection.cursor() as cursor:
        # Fetch the user's game stats
        cursor.execute("""
            SELECT id
            FROM dungeon_sword
            WHERE sword_rank = 0
            """
        )
        sword_id = cursor.fetchone()[0]
        cursor.execute("""
            SELECT id
            FROM dungeon_boots
            WHERE boots_rank = 0
            """
        )
        boots_id = cursor.fetchone()[0]
        cursor.execute("""
            SELECT id
            FROM dungeon_staff
            WHERE staff_rank = 0
            """
        )
        staff_id = cursor.fetchone()[0]
        cursor.execute("""
            SELECT id
            FROM dungeon_armor
            WHERE armor_rank = 0
            """
        )
        armor_id = cursor.fetchone()[0]
        
    return (sword_id, boots_id, staff_id, armor_id)

# Helper function for ensuring that the user has game stats.
# Call this function prior to attempting to modify game stats unless already in dungeon.
# Jason 3/1/25
def check_and_create_game_stats(user_id):
    with connection.cursor() as cursor:
        # Fetch the user's game stats
        cursor.execute("""
            SELECT *
            FROM dungeon_gamestats
            WHERE user_id = %s
            """,
            [user_id]
        )
        rows = cursor.fetchall()
        
        # If the user doesn't have game stats yet, create them
        if not rows:
            beginner_gear = get_beginner_gear_ids()
            cursor.execute("""
                INSERT INTO dungeon_gamestats 
                (user_id, max_health, coins, action_points, sword_id, boots_id, staff_id, armor_id) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                [user_id, 20, 0, 0, beginner_gear[0], beginner_gear[1], beginner_gear[2], beginner_gear[3]]
            )
            
@login_required
def task_details(request, task_pk):
    # Displays the details of a single task.
    pass    

# Displays the FitKnight's Fit-Quests (tasks) for the day
# As well as any progress on daily quests

@login_required
def view_current_tasks(request):
    # Ensure the current user is a not FitGuildOfficer.
    if request.user.user_type == 'FitGuildOfficer':
        return redirect('fitness:home')
    else:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT id, name
                FROM fitness_task
                WHERE user_id = %s
                AND days_of_week LIKE CONCAT('%%', STRFTIME('%%w', %s), '%%')
                AND STRFTIME('%%Y%%m%%d', %s) <= STRFTIME('%%Y%%m%%d', end_date)
                """,
                [request.user.id, datetime.datetime.now(), datetime.datetime.now()]
            )
            task_rows = cursor.fetchall()
            
            cursor.execute("""
                SELECT minutes_walked, water_drank_L, fruit_veggie_servings
                FROM fitness_dailylog
                WHERE user_id = %s AND DATE(time_completed) = DATE(%s)
                """,
                [request.user.id, datetime.datetime.now()]
            )
            daily_row = cursor.fetchone()
                
        # Create a dictionary of things to pass to the template for the html
        if daily_row:
            template_args = {'task_rows': task_rows, 'walk_goal': DAILY_WALK, 'water_goal': DAILY_WATER, 'fruit_veg_goal': DAILY_FRUIT_VEG, 'mins_walk': daily_row[0], 'water': daily_row[1], 'fruit_veg': daily_row[2]}
        else:
            template_args = {'task_rows': task_rows, 'walk_goal': DAILY_WALK, 'water_goal': DAILY_WATER, 'fruit_veg_goal': DAILY_FRUIT_VEG, 'mins_walk': 0, 'water': 0, 'fruit_veg': 0}
            
        return render(request, 'fitness/view_current_tasks.html', template_args)


# Implements both Report Daily Quest Completion and Update Daily Quest Completion
# Jason 3/1/25
@login_required
def complete_daily(request):
    # Ensure the current user is a not FitGuildOfficer.
    if request.user.user_type == 'FitGuildOfficer':
        return redirect('fitness:home')
    else:
        if request.method == 'GET':
            # The user is requesting the daily task completion form
            # See if they have already submitted a form today
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT minutes_walked, water_drank_L, fruit_veggie_servings
                    FROM fitness_dailylog
                    WHERE user_id = %s AND DATE(time_completed) = DATE(%s)
                    """,
                    [request.user.id, datetime.datetime.now()]
                )
                row = cursor.fetchone()
                
            # Create a dictionary of things to pass to the template for the html
            if row:
                template_args = {'mins_walk': row[0], 'water': row[1], 'fruit_veg': row[2]}
            else:
                template_args = {'mins_walk': 0, 'water': 0, 'fruit_veg': 0}
                
                    
            
            return render(request, 'fitness/complete_daily.html', template_args)
        else:
            # The user is already at the daily task completion form, trying to submit their progress with a POST request
            
            # Ensure the user has game stats to modify
            check_and_create_game_stats(request.user.id)
            
            # See if they have already submitted a form today
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT minutes_walked, water_drank_L, fruit_veggie_servings
                    FROM fitness_dailylog
                    WHERE user_id = %s AND DATE(time_completed) = DATE(%s)
                    """,
                    [request.user.id, datetime.datetime.now()]
                )
                old_daily = cursor.fetchone()
                
                cursor.execute("""
                    SELECT action_points
                    FROM dungeon_gamestats
                    WHERE user_id = %s
                    """,
                    [request.user.id]
                )
                game_stats_action = int(cursor.fetchone()[0])
                
                # There is an existing daily log, so perform an update
                if old_daily:
                    # Update the daily log
                    updated_daily = (max(old_daily[0], int(request.POST['minutes_walked'])), max(old_daily[1], float(request.POST['water_drank_L'])), max(old_daily[2], int(request.POST['fruit_veggie_servings'])))
                    
                    # Determine the number of action points to reward
                    action_points = 0
                    
                    if updated_daily[0] >= DAILY_WALK and old_daily[0] < DAILY_WALK:
                        action_points += DAILY_REWARD
                    if updated_daily[1] >= DAILY_WATER and old_daily[1] < DAILY_WATER:
                        action_points += DAILY_REWARD
                    if updated_daily[2] >= DAILY_FRUIT_VEG and old_daily[2] < DAILY_FRUIT_VEG:
                        action_points += DAILY_REWARD
                    
                    cursor.execute("""
                    UPDATE dungeon_gamestats
                    SET action_points = %s
                    WHERE user_id = %s
                    """,
                    [(game_stats_action + action_points),request.user.id]
                    )
                    
                    cursor.execute("""
                    UPDATE fitness_dailylog
                    SET minutes_walked = %s, water_drank_L = %s, fruit_veggie_servings = %s, time_completed = %s
                    WHERE user_id = %s AND DATE(time_completed) = DATE(%s)
                    """,
                    [updated_daily[0], updated_daily[1], updated_daily[2], datetime.datetime.now(), request.user.id, datetime.datetime.now()]
                    )

                # There is not an existing daily log, so create one 
                else: 
                    new_daily = (max(0, int(request.POST['minutes_walked'])), max(0, float(request.POST['water_drank_L'])), max(0, int(request.POST['fruit_veggie_servings'])))
                    
                    # Determine the number of action points to reward
                    action_points = 0
                    if new_daily[0] >= DAILY_WALK:
                        action_points += DAILY_REWARD
                    if new_daily[1] >= DAILY_WATER:
                        action_points += DAILY_REWARD
                    if new_daily[2] >= DAILY_FRUIT_VEG:
                        action_points += DAILY_REWARD
                        
                    cursor.execute("""
                    UPDATE dungeon_gamestats
                    SET action_points = %s
                    WHERE user_id = %s
                    """,
                    [(game_stats_action + action_points),request.user.id]
                    )
                    
                    cursor.execute("""
                    INSERT INTO fitness_dailylog
                    (user_id, minutes_walked, water_drank_L, fruit_veggie_servings, time_completed)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    [request.user.id, new_daily[0], new_daily[1], new_daily[2], datetime.datetime.now()]
                    )
                    
            return redirect('fitness:view_current_tasks')



@login_required
def search_knights(request):
    # Ensure the current user is a FitGuildOfficer with a gym.
    if request.user.user_type != 'FitGuildOfficer' or not request.user.gym:
        return redirect('fitness:home')

    # Get the search query from the GET request
    if request.GET.get('knight_name'):
        search_query = request.GET.get('knight_name')
    else: 
        # Specify a default empty search query
        search_query = ''
        
    # Get the page number from the GET request
    if request.GET.get('page'):
        page_number = int(request.GET.get('page'))
    else: 
        # Specify a default page number
        page_number = 1
        
    with connection.cursor() as cursor:
        # Count the number of FitKnights in this officer's gym
        cursor.execute("""
            SELECT COUNT(*)
            FROM gym_fitcrawleruser
            WHERE user_type = 'FitKnight'
              AND gym_id = %s
              AND LOWER(username) LIKE CONCAT('%%', LOWER(%s), '%%')
            """,
            [request.user.gym_id, search_query]
        )
        total = cursor.fetchone()[0]
        
        # Determine the last possible page based upon the total number of matching exercises
        last_page = ceil(total / NUM_ENTRIES_PER_PAGE)
        # Handle the case of no matching exercises to avoid page 0
        if last_page < 1:
            last_page = 1
        
        # If the page number is out of range
        if page_number / NUM_ENTRIES_PER_PAGE > total:
            # Set the page number as the last possible page number
            page_number = last_page
            
        # Calculate the offset
        offset = NUM_ENTRIES_PER_PAGE*(page_number - 1)
        
        # Fetch the matching knights
        cursor.execute("""
            SELECT id, username, email
            FROM gym_fitcrawleruser
            WHERE user_type = 'FitKnight'
              AND gym_id = %s
              AND LOWER(username) LIKE CONCAT('%%', LOWER(%s), '%%')
            ORDER BY username
            LIMIT %s
            OFFSET %s
            """,
            [request.user.gym_id, search_query, NUM_ENTRIES_PER_PAGE, offset]
        )
        rows = cursor.fetchall()
        
        
    # Create a dictionary of things to pass to the template for the html
    template_args = {'knights': rows, 'search_query': search_query, 'page_number': page_number}

    if page_number > 1:
        template_args['previous'] = page_number - 1
    if page_number < last_page:
        template_args['next'] = page_number + 1

    return render(request, 'fitness/search_knights.html', template_args)