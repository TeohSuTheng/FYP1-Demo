from django.urls import path, include
from . import views

app_name = 'PlantWebApp'

urlpatterns = [
    path('usage-tags-settings/',views.UseListApi,name='usageTagsSettings'),
]