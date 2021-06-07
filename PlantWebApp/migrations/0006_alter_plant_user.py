# Generated by Django 3.2.3 on 2021-06-07 12:15

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('PlantWebApp', '0005_alter_plant_user'),
    ]

    operations = [
        migrations.AlterField(
            model_name='plant',
            name='user',
            field=models.ForeignKey(default=26, on_delete=django.db.models.deletion.CASCADE, to='auth.user'),
            preserve_default=False,
        ),
    ]
