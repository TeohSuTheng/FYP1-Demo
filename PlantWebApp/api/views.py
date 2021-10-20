from django.http.response import JsonResponse
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.renderers import TemplateHTMLRenderer

from PlantWebApp.models import Plant
from .serializers import PlantSerializer

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

'''
@api_view(['GET'])
def UseListApi(request):
    if request.method == 'GET':
        uses = Usage.objects.all()
        serializer = UsageSerializer(uses,many=True)
        return Response(serializer.data)'''