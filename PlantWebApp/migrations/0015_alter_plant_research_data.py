# Generated by Django 3.2.3 on 2021-11-17 17:23

import ckeditor.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('PlantWebApp', '0014_alter_plant_research_data'),
    ]

    operations = [
        migrations.AlterField(
            model_name='plant',
            name='research_data',
            field=ckeditor.fields.RichTextField(blank=True, null=True),
        ),
    ]