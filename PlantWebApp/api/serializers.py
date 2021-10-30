from django.db.models import fields
from rest_framework import serializers
from PlantWebApp.models import Distribution, Plant, Profile, Usage
from django.contrib.auth.models import User

# Serialize Django object into json
class PlantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plant
        fields = ['id','plantScientificName','plantLocalName','publish','rejected'] #'__all__'

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['role_id','dept','institution'] #'__all__'

# Nested Relationships
class UserProfileSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)
    class Meta:
        model = User
        fields = ['id','username','first_name','last_name','email','profile'] #'__all__'

class UsageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usage
        fields = "__all__"

class DistributionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Distribution
        fields = "__all__"

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id','first_name','last_name']

class PlantDetailSerializer(serializers.ModelSerializer):
    usage = UsageSerializer(many = True, read_only=True)
    user = UserSerializer(read_only=True)
    distribution = DistributionSerializer(many = True, read_only=True)
    class Meta:
        model = Plant
        fields = "__all__"

# Count reverse m-2-m relationships in django rest
# https://tute.io/how-to-count-reverse-manytomany-relationships-with-django-rest-framework
class PlantDistSummarySerializer(serializers.ModelSerializer):
    num_plant = serializers.IntegerField(read_only=True)
    class Meta:
        model = Distribution
        fields = ['id','country_alpha2','countryName','num_plant',]

class SupervisorSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id','first_name','last_name'] #'__all__'

