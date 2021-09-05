from django.db.models import fields
from .models import Distribution, Plant, Rejection, Usage, Profile
from django.forms import ModelForm
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django import forms

# django-bootstrap-modal-forms
from bootstrap_modal_forms.forms import BSModalModelForm


class PlantForm(ModelForm):
    class Meta:
        model = Plant
        #fields = '__all__'  
        fields = ('plantScientificName','plantLocalName','pmStem','pmLeaf','pmFlower',
        'pmFruit','plantImg','usage','voucher_no','distribution','plantref',)
    # Widgets

class RejectForm(ModelForm):
    class Meta:
        model = Rejection
        fields = ['reason']

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

class DistributionForm(ModelForm):
    class Meta:
        model = Distribution
        fields = '__all__'

class UserUpdateForm(ModelForm):
    class Meta:
        model = User
        fields = ['first_name','last_name','username','email',]

class UseTagUpdateModelForm(BSModalModelForm):
    class Meta:
        model = Usage
        fields = '__all__' 
