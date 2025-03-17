from django.urls import path
from . import views

app_name = 'dungeon'
urlpatterns = [
    path('milestones/', views.view_milestones, name='view_milestones'),
    path('milestone/<int:milestone_pk>/', views.complete_milestone, name='complete_milestone'),
    path('inventory/', views.view_inventory, name='view_inventory'),
    path('select/', views.dungeon_select, name='dungeon_select'),
    path('begin/<int:dungeon_pk>', views.dungeon_begin_exploration, name='dungeon_begin_exploration'),
]