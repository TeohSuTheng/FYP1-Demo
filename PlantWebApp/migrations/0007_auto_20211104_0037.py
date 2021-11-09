# Generated by Django 3.2.3 on 2021-11-03 16:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('PlantWebApp', '0006_remove_plant_sv_approved'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='role',
            field=models.SmallIntegerField(choices=[(0, 'Admin'), (1, 'Committee'), (2, 'Researcher')]),
        ),
        migrations.DeleteModel(
            name='Role',
        ),
    ]