# Generated by Django 3.2.3 on 2021-11-14 06:07

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('PlantWebApp', '0010_usage_is_verified'),
    ]

    operations = [
        migrations.CreateModel(
            name='LocalDistribution',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('stateName', models.CharField(max_length=50)),
                ('plant', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='PlantWebApp.plant')),
            ],
        ),
    ]
