from django.http.response import JsonResponse
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.renderers import TemplateHTMLRenderer

from PlantWebApp.models import Plant, Profile
from django.contrib.auth.models import User
from .serializers import PlantSerializer,UserProfileSerializer
from django.contrib.postgres.search import SearchVector, SearchQuery

@api_view(['GET'])
def apiOverview(request):
    api_urls = {
        'List Published Plants': '/pub-plant-list/',
        'Plant Detail View': '/plant-detail/<str:pk>/',
        'Create' : '/plant-create/',
    }
    return Response(api_urls)

@api_view(['GET'])
def pubPlantList(request):
    if request.method == 'GET':
        plant_list = Plant.objects.filter(publish=True).order_by('plantScientificName')
        serializer = PlantSerializer(plant_list,many=True)
        return Response(serializer.data)

@api_view(['GET'])
def countryData(request,country):
    if request.method == 'GET':
        results = Plant.objects.annotate(search = SearchVector('distribution__countryName')).filter(search=SearchQuery(country)).distinct('id')
        serializer = PlantSerializer(results,many=True)
        return Response(serializer.data)

@api_view(['GET'])
def UserPersonalData(request,id):
    if request.method == 'GET':
        user_info = User.objects.get(id=id)
        serializer = UserProfileSerializer(user_info)
        return Response(serializer.data)



