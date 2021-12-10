from django.db.models import fields
from django.forms import formset_factory
from .models import Distribution, Images, LocalDistribution, Plant, Rejection, Usage, Profile, Permission
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
        fields = ('taxoKingdom','taxoDivision','taxoClass','taxoOrder','taxoFamily','taxoGenus','plantScientificName','plantLocalName','pmStem','pmLeaf','pmFlower',
        'pmFruit','plantImg','usage','voucher_no','distribution','localDistribution','plantref','research_data')
    # Widgets

class ImageForm(ModelForm):
    class Meta:
        model = Images
        fields = ['image']

class ResearchForm(ModelForm):
    class Meta:
        model = Plant
        fields = ['research_data']

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
        fields = ['first_name','last_name','username','email','password1','password2',]

class UserProfileForm(ModelForm):
    class Meta:
        model = Profile
        fields = ['institution','dept'] #'__all__'  ['institution','dept','sv_id','role'] 

class DistributionForm(ModelForm):
    class Meta:
        model = Distribution
        fields = '__all__'

class LocalDistForm(ModelForm):
    class Meta:
        model = LocalDistribution
        fields = '__all__'

class PermissionForm(ModelForm):
    class Meta:
        model = Permission
        fields = '__all__'

class UserUpdateForm(ModelForm):
    class Meta:
        model = User
        fields = ['first_name','last_name','username','email',]

class UseTagUpdateModelForm(BSModalModelForm):
    class Meta:
        model = Usage
        fields = '__all__' 

FIELD_CHOICES = [
    ('plantScientificName','Scientific Name'),
    ('plantLocalName','Local Name'),
    ('pmStem','Stem Morphology'),
]

BOOLEAN_CHOICES = [
    ('And','AND'),
    ('Or','OR'),
    ('Not','NOT'),
]

class AdvancedSearchForm(forms.Form):
    term = forms.CharField(
        label="Search",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter Search Query'
        }))
    field = forms.ChoiceField(
        label="Select Field",
        widget=forms.Select,
        choices=FIELD_CHOICES,
    )
    booleanOperator = forms.ChoiceField(
        label="Select Boolean Operator",
        widget=forms.Select,
        choices=BOOLEAN_CHOICES,
    )

#AdvancedSearchFormSet = formset_factory(AdvancedSearchForm,extra=1)