from math import ceil
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, connection

# Create your views here.

NUM_ENTRIES_PER_PAGE = 10

def redirect_home(request):
    return redirect('fitness:home')

def home(request):
    return render(request, 'fitness/home.html')

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