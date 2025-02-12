from django.urls import path
from . import views

app_name = 'gym'
urlpatterns = [
    path('logout/', views.logout, name='logout'),
    path('login/', views.login, name='login'),
    path('signup/', views.signup, name='signup'),
    path('create_gym/', views.create_gym, name='create_gym'),
    path('join_gym/', views.join_gym, name='join_gym'),
    path('list_applications/', views.list_applications, name='list_applications'),
    path('process_application/', views.process_application, name='process_application'),
]