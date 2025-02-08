from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager


# Create your models here.

class FitUserManager(BaseUserManager):
    # This method creates a regular user
    def create_user(self, username, email, password=None, **otherfields):
        if not username:
            raise ValueError('Must have a username!')
        if not email:
            raise ValueError('Must have an email!')
        
        new_user = self.model(
            username=username,
            email=self.normalize_email(email),
            **otherfields
        )
        
        new_user.set_password(password)
        new_user.save(using=self._db)
        return new_user
    
    # This method creates a superuser (an admin)
    def create_superuser(self, username, email, password=None):
        new_user = self.create_user(username, email, password)
        new_user.is_superuser = True
        new_user.is_admin = True
        new_user.is_active = True
        new_user.save(using=self._db)
        return new_user
    

class FitCrawlerUser(AbstractBaseUser):
    # PK is automatically handled by Django (the pk field is named id)
    
    email = models.EmailField(max_length=255, unique=True)
    username = models.CharField(max_length=63, unique=True)
    
    TYPES = ( ('FitKnight', 'FitKnight'), ('FitGuildOfficer', 'FitGuildOfficer'))
    
    user_type = models.CharField(max_length=31, choices=TYPES, default='FitKnight')
    
    # Use gym_id for database lookups
    gym = models.ForeignKey('gym.Gym', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Password Field is inherited from AbstractBaseUser
    
    # Fields necessary for Django admin backend
    is_admin = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    # These seem to be specified so that AbstractBaseUser knows which fields to link up
    USERNAME_FIELD = 'username'
    EMAIL_FIELD = 'email'
    REQUIRED_FIELDS = ['email']
    
    # Define the manager which will handle account creation
    objects = FitUserManager()
    
    def __str__(self):
        return self.username
    
    # These methods appear to be necessary for the Django admin backend to work
    def has_perm(self, perm, obj=None):
        return True
    
    def has_module_perms(self, app_label):
        return True
    
    @property
    def is_staff(self):
        return self.is_admin
    

    

class Gym(models.Model):
    # PK is automatically handled by Django (the pk is the same as the owner's id)
    
    # Specify columns for the table in the database
    name = models.CharField(max_length=255)
    description = models.TextField(max_length=511, blank=True)
    join_code = models.CharField(max_length=31, unique=True)
    owner = models.OneToOneField(FitCrawlerUser, on_delete=models.CASCADE, related_name='owned_gym', primary_key=True)
    
    def __str__(self):
        return self.name
    
class GymApplication(models.Model):
    # PK is automatically handled by Django
    applicant = models.ForeignKey(FitCrawlerUser, on_delete=models.CASCADE)
    destination = models.ForeignKey(Gym, on_delete=models.CASCADE)
    
    def __str__(self):
        return str(self.applicant) + ' -> ' + str(self.destination)