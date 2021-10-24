from django.urls import path, include
from . import views


app_name = 'PlantWebApp'

urlpatterns = [
    path('',views.apiOverview, name='apiOverview'),
    path('browse-name-api/',views.pubPlantList, name='pubPlantList'),
    path('browse-country-api/<str:country>',views.countryData, name='countryData'),
    #path('usage-tags-settings/',views.UseListApi,name='usageTagsSettings'),
]
