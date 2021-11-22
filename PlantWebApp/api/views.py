from django.http.response import JsonResponse
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.renderers import TemplateHTMLRenderer

from PlantWebApp.models import Distribution, Plant, Profile, Images, LocalDistribution
from django.contrib.auth.models import User
from .serializers import LocalDistributionSerializer, UserSerializer,PlantSerializer,UserProfileSerializer,PlantDetailSerializer, PlantDistSummarySerializer
from django.contrib.postgres.search import SearchVector, SearchQuery
from rest_framework.pagination import PageNumberPagination
from django.db.models import Count

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
        paginator = PageNumberPagination()
        paginator.page_size = 10

        plant_list = Plant.objects.filter(publish=True).order_by('plantScientificName')
        result_page = paginator.paginate_queryset(plant_list, request) 
        serializer = PlantSerializer(result_page,many=True)
        
        return paginator.get_paginated_response(serializer.data)

@api_view(['GET'])
def countryData(request,country):
    if request.method == 'GET':
        results = Plant.objects.annotate(search = SearchVector('distribution__countryName')).filter(search=SearchQuery(country)).distinct('id')
        serializer = PlantSerializer(results,many=True)
        return Response(serializer.data)

@api_view(['GET'])
def usageData(request,use):
    if request.method == 'GET':
        results = Plant.objects.annotate(search = SearchVector('usage__usage_tag')).filter(search=SearchQuery(use)).distinct('id')
        serializer = PlantSerializer(results,many=True)
        return Response(serializer.data)

@api_view(['GET'])
def UserPersonalData(request,id):
    if request.method == 'GET':
        user_info = User.objects.get(id=id)
        serializer = UserProfileSerializer(user_info)
        return Response(serializer.data)

@api_view(['GET'])
def PlantDetail(request,id):
    if request.method == 'GET':
        plantdata = Plant.objects.get(id=id)
        serializer = PlantDetailSerializer(plantdata)
        return Response(serializer.data)

@api_view(['GET'])
def PlantDistSummary(request):
    if request.method == 'GET':
        distData = Distribution.objects.annotate(num_plant=Count('plant'),).order_by('-num_plant') # Get total number of plant records based on each country (plant distribution) and order by plant count in distribution model in desc '-'
        serializer = PlantDistSummarySerializer(distData, many=True)
        return Response(serializer.data)

@api_view(['GET'])
def PlantLocalDistSummary(request):
    if request.method == 'GET':
        distData = LocalDistribution.objects.annotate(num_plant=Count('plant'),).order_by('-num_plant') # Get total number of plant records based on each country (plant distribution) and order by plant count in distribution model in desc '-'
        serializer = LocalDistributionSerializer(distData, many=True)
        return Response(serializer.data)

@api_view(['GET'])
def UserPermission(request,id):
    if request.method == 'GET':
        user_list = User.objects.filter(profile__role=2).filter(profile__is_verified=True).exclude(id=request.user.id).exclude(permission__plantID=id) #list of researchers
        serializer = UserSerializer(user_list, many=True)
        return Response(serializer.data)

'''
@api_view(['GET'])
def SupervisorList(request):
    if request.method == 'GET':
        user_info = User.objects.filter(profile__role_id=2)
        serializer = SupervisorSerializer(user_info, many=True)
        return Response(serializer.data)
'''

@api_view(["DELETE"])
def image_delete_rest_endpoint(request, id):
    Images.objects.get(id=id).delete()
    return Response()