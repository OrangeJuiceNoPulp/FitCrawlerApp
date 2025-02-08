from django.shortcuts import render, redirect
from django.http import HttpResponse

# Create your views here.

def redirect_home(request):
    return redirect('fitness:home')

def home(request):
    return render(request, 'fitness/home.html')