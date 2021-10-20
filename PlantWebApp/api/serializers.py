from rest_framework import serializers
from PlantWebApp.models import Plant

# Serialize Django object into json
class PlantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plant
        fields = '__all__'