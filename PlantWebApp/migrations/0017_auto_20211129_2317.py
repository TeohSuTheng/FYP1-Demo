# Generated by Django 3.2.3 on 2021-11-29 15:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('PlantWebApp', '0016_auto_20211118_2312'),
    ]

    operations = [
        migrations.AddField(
            model_name='plant',
            name='collection_extract',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='plant',
            name='collection_powder',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='plant',
            name='collection_specimen',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]