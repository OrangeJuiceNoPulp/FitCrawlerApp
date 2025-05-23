from django.urls import path
from . import views

app_name = 'gym'
urlpatterns = [
    path('logout/', views.logout, name='logout'),
    path('login/', views.login, name='login'),
    path('signup/', views.signup, name='signup'),
    path('change_password/', views.change_password, name='change_password'),
    path('create_gym/', views.create_gym, name='create_gym'),
    path('join_gym/', views.join_gym, name='join_gym'),
    path('list_applications/', views.list_applications, name='list_applications'),
    path('process_application/', views.process_application, name='process_application'),
    path('search_knights/', views.search_knights, name='search_knights'),
    path('remove_member/<int:knight_id>/', views.remove_member, name='remove_member'),
]