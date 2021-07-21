from import_export import resources
from .models import Distribution

class DistResource(resources.ModelResource):
    class meta:
        model = Distribution