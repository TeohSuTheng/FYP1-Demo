from django.contrib import admin
from . import models

# Register your models here.
admin.site.register(models.Plant)
admin.site.register(models.Profile)
admin.site.register(models.Usage)
admin.site.register(models.Distribution)
admin.site.register(models.LocalDistribution)
admin.site.register(models.Images)
admin.site.register(models.Rejection)
admin.site.register(models.Plant_Usage)
admin.site.register(models.Plant_Distribution)
admin.site.register(models.Plant_LocalDistribution)
admin.site.register(models.Permission)