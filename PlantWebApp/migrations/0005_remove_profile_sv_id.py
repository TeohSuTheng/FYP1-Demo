# Generated by Django 3.2.3 on 2021-11-01 13:37

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('PlantWebApp', '0004_delete_recordpermission'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='profile',
            name='sv_id',
        ),
    ]
