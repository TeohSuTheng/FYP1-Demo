from import_export import resources
from .models import Distribution, Plant

class DistResource(resources.ModelResource):
    class meta:
        model = Distribution

class PlantResource(resources.ModelResource):
    class meta:
        model = Plant