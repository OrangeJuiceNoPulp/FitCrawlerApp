from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, connection

from fitness.views import check_and_create_game_stats, TASK_COMPLETION_REQUIREMENT

import datetime

# Create your views here.

# Helper function for getting player inventory contents
# - Jason 3/16/25
def get_player_inventory(id):
    player_inventory = {}
    with connection.cursor() as cursor:
        # Select the contents of the user's inventory
        cursor.execute("""
            SELECT u.username, g.max_health, g.action_points, g.coins,
                       sw.name, sw.sword_rank, sw.strength_boost, sw.sprite_path,
                       b.name, b.boots_rank, b.ap_reduction_factor, b.sprite_path,
                       st.name, st.staff_rank, st.healing_factor, st.sprite_path,
                       a.name, a.armor_rank, a.defense_factor, a.sprite_path
            FROM dungeon_gamestats g JOIN dungeon_sword sw ON g.sword_id = sw.id
                       JOIN dungeon_boots b ON g.boots_id = b.id
                       JOIN dungeon_staff st ON g.staff_id = st.id
                       JOIN dungeon_armor a ON g.armor_id = a.id
                       JOIN gym_fitcrawleruser u ON g.user_id = u.id
            WHERE g.user_id = %s
            """, [id])
        inventory_info = cursor.fetchone()

        sword_path = 'dungeon/sword/default.png'
        boots_path = 'dungeon/boots/default.png'
        staff_path = 'dungeon/staff/default.png'
        armor_path = 'dungeon/armor/default.png'

        if inventory_info[7]:
            sword_path = 'dungeon/sword/' + inventory_info[7]
        if inventory_info[11]:
            boots_path = 'dungeon/boots/' + inventory_info[11]
        if inventory_info[15]:
            staff_path = 'dungeon/staff/' + inventory_info[15]
        if inventory_info[19]:
            armor_path = 'dungeon/armor/' + inventory_info[19]

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



# WIP for dungeon crawler implementation
# - Jason 3/16/25
@login_required
def dungeon_select(request):
    with connection.cursor() as cursor:
        # Select a list of dungeons for the user to choose from
        cursor.execute("""
            SELECT d.id, d.name, d.description, d.difficulty_score, d.sprite_folder
            FROM dungeon_dungeon d
            ORDER BY d.name
            """)
        dungeon_info = cursor.fetchall()

    template_args = {'dungeon_info': dungeon_info}

    return render(request, 'dungeon/dungeon_select.html', template_args)

# WIP for dungeon crawler implementation
# - Jason 3/16/25
@login_required
def dungeon_begin_exploration(request, dungeon_pk):
    pass


# This view allows for the user to view their inventory contents
# - Jason 3/16/25
@login_required
def view_inventory(request):
    # Ensure that the user has gamestats
    check_and_create_game_stats(request.user.id)

    inventory = get_player_inventory(request.user.id)

    return render(request, 'dungeon/view_inventory.html', inventory)

# This function allows for the user to view the milestones and rewards.
# - Jason 3/8/25, Updated Jason 3/16/25
@login_required
def view_milestones(request):
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

            print('checking for completion...')

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