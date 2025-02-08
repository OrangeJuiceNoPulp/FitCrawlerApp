from django import forms
from django.contrib import admin
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError


from gym.models import *

# Register your models here.

class UserCreationForm(forms.ModelForm):
    
    password1 = forms.CharField(label="Password", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Confirm Password", widget=forms.PasswordInput)
    
    class Meta:
        model = FitCrawlerUser
        fields = ['username', 'email']

    def confirm_password(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        
        # Ensure that both password1 and password2 are not empty, 
        # and then ensure they match
        if password1 and password2 and (password1 != password2):
            raise ValidationError('Passwords do not match!')
        
        return password2
    
    def save(self, commit=True):
        user = super().save(commit=False)
        # Hash the password before saving it
        user.set_password(self.cleaned_data['password2'])
        if commit:
            user.save()
        return user
    
class UserChangeForm(forms.ModelForm):
    password = ReadOnlyPasswordHashField()
    
    class Meta:
        model = FitCrawlerUser
        fields = ['username', 'email', 'user_type', 'gym', 'is_admin']
        
class FitCrawlerUserAdmin(UserAdmin):
    # Forms for adding and changing user instances
    form = UserChangeForm
    add_form = UserCreationForm
    
    list_display = ['id','username', 'email', 'user_type', 'gym', 'is_admin']
    list_filter = ['user_type', 'is_admin']
    
    fieldsets = [
        (None, {'fields': ['username', 'email', 'password']}),
        ('User Type', {'fields': ['user_type']}),
        ('Gym', {'fields': ['gym']}),
        ('Permissions', {'fields': ['is_admin']}),
    ]
    
    add_fieldsets = [
        (None, {
            'classes': ['wide'],
            'fields': ['username', 'email', 'password1', 'password2']
        })
    ]
    
    search_fields = ['username', 'email']
    
    ordering = ['username']
    filter_horizontal = []
    
# Register the custom user model (FitCrawlerUser) and the admin handling
admin.site.register(FitCrawlerUser, FitCrawlerUserAdmin)

# Django's Group model is not being used with the custom user, so unregister it.
admin.site.unregister(Group)

# Register the gym model
admin.site.register(Gym)
admin.site.register(GymApplication)