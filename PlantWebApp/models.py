from django.db import models
from datetime import datetime, date
#from django.contrib.auth.models import User

# Create your models here.
class Usage(models.Model):
    usage_tag = models.CharField(max_length=255)

class Plant(models.Model):
    plantScientificName =  models.CharField(max_length=255,unique=True)
    plantLocalName = models.TextField(null=True, blank=True)
    pmStem = models.TextField(null=True, blank=True)
    pmLeaf = models.TextField(null=True, blank=True)
    pmFlower = models.TextField(null=True, blank=True)
    pmFruit = models.TextField(null=True, blank=True)
    plantImg = models.ImageField(blank=True,upload_to='plantImg/',default='default.jpeg') #'images/'
    usetemp = models.TextField(null=True, blank=True)
    usage = models.ManyToManyField(
        Usage,
        through="Plant_Usage",
        blank=True
    )
    #user = models.ForeignKey(User,on_delete=models.CASCADE) #when we delete user, data still remains o - session
    voucher_no = models.CharField(max_length=100, null=True, blank=True)
    plantDist = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    plantref = models.TextField(null=True, blank=True)
    #planttemp = models.TextField(null=True, blank=True)
    #**#ref
    #publish = False (by default)
    #published_at
    #updated_at = models.DateTimeField(auto_now=True)

class Plant_Usage(models.Model):
    plantID = models.ForeignKey(Plant,on_delete=models.CASCADE)
    usageID = models.ForeignKey(Usage,on_delete=models.CASCADE)

