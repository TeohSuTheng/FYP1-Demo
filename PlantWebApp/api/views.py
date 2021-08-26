from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.renderers import TemplateHTMLRenderer

from PlantWebApp.models import Usage
from .serializers import UsageSerializer

@api_view(['GET'])
def UseListApi(request):
    if request.method == 'GET':
        uses = Usage.objects.all()
        serializer = UsageSerializer(uses,many=True)
        return Response(serializer.data)