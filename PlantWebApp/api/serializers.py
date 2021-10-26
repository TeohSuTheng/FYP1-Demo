from rest_framework import serializers
from PlantWebApp.models import Plant, Profile
from django.contrib.auth.models import User

# Serialize Django object into json
class PlantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plant
        fields = ['id','plantScientificName','plantLocalName','publish','rejected'] #'__all__'

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['role','dept','institution'] #'__all__'

# Nested Relationships
class UserProfileSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)
    class Meta:
        model = User
        fields = ['id','username','first_name','last_name','email','profile'] #'__all__'


'''class PlantDetailSerializer(serializers.Serializer):
    plantScientificName =  serializers.CharField(max_length=255,unique=True)
    plantLocalName = serializers.TextField(null=True, blank=True)
    pmStem = serializers.TextField(null=True, blank=True)
    pmLeaf = serializers.TextField(null=True, blank=True)
    pmFlower = serializers.TextField(null=True, blank=True)
    pmFruit = serializers.TextField(null=True, blank=True)
    plantImg = serializers.ImageField(blank=True,upload_to='plantImg/',default='default.jpeg') #'images/'
    #usage = 
    #user
    voucher_no = serializers.CharField(max_length=100, null=True, blank=True)
    #distribution 
    created_at = serializers.DateTimeField(auto_now_add=True)
    plantref = serializers.TextField(null=True, blank=True)
    publish = serializers.BooleanField(default=False)
    rejected = serializers.BooleanField(default=False)
    updated_at = serializers.DateTimeField(auto_now=True)'''

