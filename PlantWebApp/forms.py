from django.db.models import fields
from .models import Plant, Usage, Profile
from django.forms import ModelForm
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django import forms


class PlantForm(ModelForm):
    class Meta:
        model = Plant
        fields = '__all__'  
        #fields = ('plant_genus','plant_species','plant_localName',) #usage

    # Widgets

class UsageForm(ModelForm):
    class Meta:
        model = Usage
        fields = '__all__' 

class CreateUserForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['first_name','last_name','username','email','password1','password2']

class UserProfileForm(ModelForm):
    class Meta:
        model = Profile
        fields = ['institution','dept','role'] #'__all__' 



