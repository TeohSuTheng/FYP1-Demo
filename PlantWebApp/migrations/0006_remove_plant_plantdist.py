# Generated by Django 3.2.3 on 2021-08-10 10:19

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('PlantWebApp', '0005_rename_user_rejection_plant'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='plant',
            name='plantDist',
        ),
    ]