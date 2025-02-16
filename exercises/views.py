from django.http import Http404
from django.shortcuts import render, redirect
from django.db import IntegrityError, connection

from django.urls import reverse
from urllib.parse import urlencode

from django.contrib.auth.decorators import login_required

from math import ceil

# Create your views here.

homepage_url = 'fitness:home'

# 10 is the current default. We might want to increase this in the future.
NUM_ENTRIES_PER_PAGE = 10


# Creates an exercise in the database.
# Jason 2/14/25
@login_required
def create_exercise(request):
    # User must be a FitGuildOfficer
    if request.user.user_type != "FitGuildOfficer":
            # If not, then redirect to the homepage
            return redirect(homepage_url)
    else:
        if request.method == 'GET':
            # The user is requesting the create exercise page
            return render(request, 'exercises/create_exercise.html')
        else:
            # The user is already at the create exercise page, trying to create an exercise with a POST request
            with connection.cursor() as cursor:
                #
                cursor.execute("INSERT INTO exercises_exercise (name, description) VALUES (%s, %s)", [request.POST['exercise_name'],request.POST['description']])
    
                # Redirect the user to the search exercises page, searching for the recently created exercise
                return redirect(reverse('exercises:search_exercises') + '?' + urlencode({'exercise_name':request.POST['exercise_name']}))
            

# For getting the search query from the GET request, the following article was referenced
# https://vindevs.com/blog/the-ultimate-guide-8-easy-steps-to-get-url-parameters-in-django-p52/

# Searches for exercises in the database whose names contain a given substring.
# Parameters from GET requests can be obtained using "request.GET.get('parameter')"
# This method should be used for search query string and page numbers.
# Basic page number functionality has been implemented, but the code does not look the cleanest.
# Jason 2/14/25
@login_required
def search_exercises(request):
    # Get the search query from the GET request
    if request.GET.get('exercise_name'):
        search_query = request.GET.get('exercise_name')
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
        # Count the number of matching exercises
        cursor.execute("""
            SELECT COUNT(*)
            FROM exercises_exercise e
            WHERE e.name LIKE CONCAT('%%', LOWER(%s), '%%')
            """, [search_query])
        
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
        
        # Fetch the relevant exercises
        cursor.execute("""
            SELECT e.id, e.name
            FROM exercises_exercise e
            WHERE e.name LIKE CONCAT('%%', LOWER(%s), '%%')
            ORDER BY e.name
            LIMIT 10 OFFSET %s
            """, [search_query, offset])
        rows = cursor.fetchall()
        
        
    # Create a dictionary of things to pass to the template for the html
    template_args = {'exercises': rows, 'search_query': search_query, 'page_number': page_number}
    if page_number > 1:
        template_args['previous'] = page_number - 1
    if page_number < last_page:
        template_args['next'] = page_number + 1
    return render(request, 'exercises/search_exercises.html', template_args)
        


@login_required
def view_exercise(request, exercise_pk):
    # Displays the details of a single Exercise.
    
    with connection.cursor() as cursor:
        # Fetch the exercise row by ID
        cursor.execute("""
            SELECT id, name, description
            FROM exercises_exercise
            WHERE id = %s
            """,[exercise_pk])
        row = cursor.fetchone()

    if not row:
        # If no matching exercise, raise 404 or redirect
        raise Http404("Exercise not found.")

    # row is (id, name, description)
    context = {
        'exercise_id': row[0],
        'exercise_name': row[1],
        'exercise_description': row[2],
    }

    return render(request, 'exercises/view_exercise.html', context)