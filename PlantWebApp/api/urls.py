from django.urls import path, include
from . import views


app_name = 'PlantWebApp'

urlpatterns = [
    path('',views.apiOverview, name='apiOverview'),
    path('browse-name-api/',views.pubPlantList, name='pubPlantList'),
    path('browse-country-api/<str:country>',views.countryData, name='countryData'),
    path('browse-usage-api/<str:use>',views.usageData, name='usageData'),
    path('user-data-api/<int:id>',views.UserPersonalData, name='userPersonalData'),
    path('plant-detail-api/<int:id>',views.PlantDetail, name='plantDetail'),
    path('plant-dist-api/',views.PlantDistSummary, name='PlantDistSummary'),
    #path('sv-api/',views.SupervisorList, name='SupervisorList'),
    path('images-api/<int:id>',views.image_delete_rest_endpoint, name='Images'),
    
    #path('usage-tags-settings/',views.UseListApi,name='usageTagsSettings'),
]
