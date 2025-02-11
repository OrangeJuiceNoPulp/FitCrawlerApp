from django.shortcuts import render, redirect, get_object_or_404
from django.db import IntegrityError, connection

from django.contrib.auth.decorators import login_required
from django.contrib.auth import login as login_user, logout as logout_user, authenticate

from gym.models import FitCrawlerUser, Gym, GymApplication

# Create your views here.

# URL for the homepage, made as a variable in case we decide to change the URL later
homepage_url = 'fitness:home'

# STEW Project Code (Previous Class Project For A School Course System like Moodle) 
# and Django Docs referenced for the creation of the
# following User Login/Logout/Signup System Functionality backend; however,
# various aspects had to be changed in order to fit the needs of this project,
# because this project is a completely different project.
# Additionally, these functionalities are said to not count as features in the project
# according to the project guidelines.
# Jason 2/8/25
# https://github.com/OrangeJuiceNoPulp/stew3/
# https://docs.djangoproject.com/en/5.1/intro/tutorial01/
# https://docs.djangoproject.com/en/5.1/topics/auth/default/
# https://docs.djangoproject.com/en/5.1/topics/auth/customizing/

@login_required
def logout(request):
    if request.method == 'POST':
        logout_user(request)
        # Redirect the user to the home page after logging out
        return redirect(homepage_url)

def login(request):
    # Ensure the user is not already logged in
    if request.user.is_authenticated:
        # Otherwise, redirect them to the home page
        return redirect(homepage_url)
    
    if request.method == 'GET':
        # The user is requesting the login page
        return render(request, 'gym/login.html')
    
    else:
        # The user is already at the login page, trying to login with a POST request
        user = authenticate(request, username=request.POST['username'], password=request.POST['password'])
        if user is not None:
            # User is successfully authenticated, so log in the user
            login_user(request, user)
            # Redirect the user to the home page
            return redirect(homepage_url)
        else:   
            # User failed to authenticate
            return render(request, 'gym/login.html', {'error':'Incorrect Username or Password'})
        
def signup(request):
    # Ensure the user is not already logged in
    if request.user.is_authenticated:
        # Otherwise, redirect them to the home page
        return redirect(homepage_url)
    
    if request.method == 'GET':
        # The user is requesting the signup page
        return render(request, 'gym/signup.html')
    else:
        # The user is already at the signup page, trying to signup with a POST request
        
        # Ensure passwords match
        if request.POST['password1'] == request.POST['password2']:
            try:
                # Create the user
                user = FitCrawlerUser.objects.create_user(
                    request.POST['username'],
                    request.POST['email'],
                    request.POST['password1'],
                    user_type = request.POST['user_type']
                )
                # The create_user method automatically saves the user in the database.
                # If any changes are made to the user here outside of the create_user method,
                # it will be necessary to save the user.
                
                # Login as the newly created user
                login_user(request, user)
                # Redirect the user to the home page
                return redirect(homepage_url)
            except IntegrityError:
                # IntegrityError will occur because either the username or email is not unique in the database, 
                # so the user will fail to be created
                return render(request, 'gym/signup.html', {'error':'The provided email address or username is already in use!'})
        else:
            # Passwords didn't match, so display an error
            return render(request, 'gym/signup.html', {'error':'Passwords did not match!'})
    

# The below features are new to this project, only Django Docs were referenced when necessary.
# https://docs.djangoproject.com/en/5.1/topics/db/sql/
# https://docs.djangoproject.com/en/5.1/intro/tutorial02/
# https://docs.djangoproject.com/en/5.1/ref/models/fields/

# Creates a Gym with the current user as the Gym Owner.
# When Owner's account is deleted, the Gym is deleted.
# When the Gym is deleted, the Owner's Gym is set to NULL.
# Jason 2/8/25
@login_required
def create_gym(request):
    if (request.user.user_type != "FitGuildOfficer") or (request.user.gym):
            # Redirect to home page if the user is not a FitGuildOfficer
            # or if the user already has a gym
            return redirect(homepage_url)
    else:
        if request.method == 'GET':
            # The user is requesting the create gym page
            return render(request, 'gym/create_gym.html')
        else:
            # The user is already at the create gym page, trying to create a gym with a POST request
            
            # Ensure the join code is not taken
            if Gym.objects.raw("SELECT * FROM gym_gym WHERE join_code = %s", [request.POST['code']]):
                # The join code is taken, so return an error
                return render(request, 'gym/create_gym.html', {'error':'The specified join code is already in use!'})
            else:
                # The join code is not taken, so continue with signup
                with connection.cursor() as cursor:
                    cursor.execute("INSERT INTO gym_gym (name, description, join_code, owner_id) VALUES (%s, %s, %s, %s)", [request.POST['gym_name'],request.POST['description'],request.POST['code'], request.user.id])
                    cursor.execute("UPDATE gym_fitcrawleruser SET gym_id = %s WHERE id = %s", [request.user.id, request.user.id])
    
                # Redirect the user to the home page
                return redirect(homepage_url)
                

# Creates a Gym Application for the current user with the input Gym Join Code (which is unique)
# Gym Applications are deleted if either the user or gym are deleted.
# Users can only have one gym at once, but can apply to many gyms.
# When implementing the Gym Application Acceptance functionality,
# it will be necessary to delete all the Gym Applications for the accepted user.
# Jason 2/8/25
@login_required
def join_gym(request):
    if request.user.gym:
        # Redirect to home page if the user already has a gym
        return redirect(homepage_url)
    else:
        if request.method == 'GET':
            # The user is requesting the join gym page
            return render(request, 'gym/join_gym.html')
        else:
            # The user is already at the join gym page, trying to join a gym with a POST request
            with connection.cursor() as cursor:
                cursor.execute("SELECT name, owner_id FROM gym_gym WHERE join_code = %s", [request.POST['code']])
                gym_info = cursor.fetchone()
            
                if gym_info:
                    # If there is a gym with that join code, ensure an application does not already exist
                    cursor.execute("SELECT * FROM gym_gymapplication WHERE applicant_id = %s AND destination_id = %s", [request.user.id, gym_info[1]])
                    existing_application = cursor.fetchone()
                    if existing_application:
                        # The user already has an open application for this gym, so display an error message
                        return render(request, 'gym/join_gym.html', {'error':'You have already applied to this gym!'})
                    else:
                        # create the application
                        cursor.execute("INSERT INTO gym_gymapplication (applicant_id, destination_id) VALUES (%s, %s)", [request.user.id, gym_info[1]])
                        success_message = 'Applied to '+ gym_info[0] + '.'
                        return render(request, 'gym/join_gym.html', {'success': success_message})
                else:
                    # Otherwise return an error message
                    return render(request, 'gym/join_gym.html', {'error':'Code is incorrect!'})
            
@login_required
def accept_application(request, application_id):
    # Accept a FitKnight's gym application and make them a member of the gym
    # owned by the current user (who must be a FitGuildOfficer).

    # Must be an officer who owns a gym
    if request.user.user_type != 'FitGuildOfficer' or not request.user.gym:
        return redirect('fitness:home')

    # Using the ORM just to verify the application:
    application = get_object_or_404(GymApplication, pk=application_id)

    # Ensure the application is for the current user's gym
    if application.destination_id != request.user.gym.owner_id:
        return redirect('fitness:home')
    
    if request.method == 'POST':
        with connection.cursor() as cursor:
            # 1) Update the applicant's gym_id
            cursor.execute("""
                UPDATE gym_fitcrawleruser
                SET gym_id = %s
                WHERE id = %s""",
                [request.user.gym.owner_id, application.applicant_id])

            # 2) Delete all applications from that applicant
            cursor.execute("""
                DELETE FROM gym_gymapplication
                WHERE applicant_id = %s""",
                [application.applicant_id])

        return redirect('fitness:home')

    return render(request, 'gym/accept_app.html', {'application': application})