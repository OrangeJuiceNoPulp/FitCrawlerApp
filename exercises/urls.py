from django.urls import path
from . import views

app_name = 'exercises'

urlpatterns = [
    path('create/', views.create_exercise, name='create_exercise'),
    path('search/', views.search_exercises, name='search_exercises'),
    path('exercise/<int:exercise_pk>/', views.view_exercise, name='view_exercise'),
]