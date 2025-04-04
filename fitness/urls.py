from django.urls import path
from . import views

app_name = 'fitness'
urlpatterns = [
    path('', views.home, name='home'),
    path('fitquests/', views.view_current_tasks, name='view_current_tasks'),
    path('daily/', views.complete_daily, name='complete_daily'),
    path('task/<int:task_pk>/', views.task_details, name='task_details'),
    path('task/<int:task_pk>/complete/', views.complete_task, name='complete_task'),
    path('assign-task/<int:knight_id>/', views.assign_task, name='assign_task_for_knight'),
    path('profile/', views.profile , name='profile'),
    path('pfp/<int:profile_pic>/', views.set_profile_picture, name='set_profile_picture'),
    
]