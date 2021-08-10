from django.db import models
from datetime import datetime, date
from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User


class Profile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    role = models.CharField(max_length=255)
    dept = models.CharField(max_length=255)
    institution = models.CharField(max_length=255)

'''
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()
'''

class Usage(models.Model):
    usage_tag = models.CharField(max_length=255,unique=True)

class Distribution(models.Model):
    country_alpha2 = models.CharField(max_length=2)
    countryName = models.CharField(max_length=100)

class Plant(models.Model):
    plantScientificName =  models.CharField(max_length=255,unique=True)
    plantLocalName = models.TextField(null=True, blank=True)
    pmStem = models.TextField(null=True, blank=True)
    pmLeaf = models.TextField(null=True, blank=True)
    pmFlower = models.TextField(null=True, blank=True)
    pmFruit = models.TextField(null=True, blank=True)
    plantImg = models.ImageField(blank=True,upload_to='plantImg/',default='default.jpeg') #'images/'
    usage = models.ManyToManyField(
        Usage,
        through="Plant_Usage",
        blank=True
    )
    user= models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
    )
    voucher_no = models.CharField(max_length=100, null=True, blank=True)
    distribution = models.ManyToManyField(
        Distribution,
        through="Plant_Distribution",
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    plantref = models.TextField(null=True, blank=True)
    publish = models.BooleanField(default=False)
    rejected = models.BooleanField(default=False)

    #planttemp = models.TextField(null=True, blank=True)
    #**#ref
    #published_at
    #updated_at = models.DateTimeField(auto_now=True)
    #usetemp = models.TextField(null=True, blank=True)

class Rejection(models.Model):
    plant = models.OneToOneField(
        Plant,
        on_delete=models.CASCADE,
    )
    reason = models.TextField(null=True, blank=True)
    
# Bridge entity for plant and usage
class Plant_Usage(models.Model):
    plantID = models.ForeignKey(Plant,on_delete=models.CASCADE)
    usageID = models.ForeignKey(Usage,on_delete=models.CASCADE)

# Bridge entity for plant and distribution
class Plant_Distribution(models.Model):
    plantID = models.ForeignKey(Plant,on_delete=models.CASCADE)
    distID = models.ForeignKey(Distribution,on_delete=models.CASCADE)