from django.urls import path
from . import views

app_name = 'fitness'
urlpatterns = [
    path('', views.home, name='home'),
    path('search_knights/', views.search_knights, name='search_knights'),
    path('fitquests/', views.view_current_tasks, name='view_current_tasks'),
    path('daily/', views.complete_daily, name='complete_daily'),
    path('fitquest/<int:task_pk>/', views.task_details, name='task_details'),
    
]