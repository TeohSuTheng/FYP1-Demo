from django.urls import path, include
from . import views


app_name = 'PlantWebApp'

urlpatterns = [
    path('',views.apiOverview, name='apiOverview'),
    path('browse-name-api/',views.pubPlantList, name='pubPlantList'),
    #path('usage-tags-settings/',views.UseListApi,name='usageTagsSettings'),
]
