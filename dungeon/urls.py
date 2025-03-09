from django.urls import path
from . import views

app_name = 'dungeon'
urlpatterns = [
    path('milestones/', views.view_milestones, name='view_milestones'),
    path('milestone/<int:milestone_pk>/', views.complete_milestone, name='complete_milestone'),
]