# Generated by Django 3.2.3 on 2021-11-01 11:48

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('PlantWebApp', '0003_plant_research_data'),
    ]

    operations = [
        migrations.DeleteModel(
            name='RecordPermission',
        ),
    ]