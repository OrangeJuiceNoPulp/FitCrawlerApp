from django.urls import path
from . import views

app_name = 'fitness'
urlpatterns = [
    path('', views.home, name='home'),
    path('search_knights/', views.search_knights, name='search_knights'),
    
]