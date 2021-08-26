from rest_framework import serializers
from PlantWebApp.models import Usage

class UsageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usage
        fields = '__all__'