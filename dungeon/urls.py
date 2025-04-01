from django.urls import path
from . import views

app_name = 'dungeon'
urlpatterns = [
    path('milestones/', views.view_milestones, name='view_milestones'),
    path('milestone/<int:milestone_pk>/', views.complete_milestone, name='complete_milestone'),
    path('inventory/', views.view_inventory, name='view_inventory'),
    path('select/', views.dungeon_select, name='dungeon_select'),
    path('begin/<int:dungeon_pk>/', views.dungeon_begin_exploration, name='dungeon_begin_exploration'),
    path('explore/', views.dungeon_view, name='dungeon_view'),
    path('traverse/<str:direction>', views.dungeon_traverse, name='dungeon_traverse'),
    path('rotate/<str:direction>', views.dungeon_rotate, name='dungeon_rotate'),
    path('leave/', views.dungeon_exit, name='dungeon_exit'),
    path('heal/', views.heal, name='heal'),
    path('death/', views.death_screen, name='death_screen'),
    path('retreat/', views.battle_retreat, name='battle_retreat'),
    path('attack/', views.battle_attack, name='battle_attack'),
    path('battle/', views.dungeon_battle_view, name='dungeon_battle'),
    path('chest/', views.open_chest, name='open_chest'),
    path('complete/', views.complete_screen, name='complete_screen'),
    path('exit/', views.exit_screen, name='exit_screen'),
]