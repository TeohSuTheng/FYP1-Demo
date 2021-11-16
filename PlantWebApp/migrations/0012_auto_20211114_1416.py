# Generated by Django 3.2.3 on 2021-11-14 06:16

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('PlantWebApp', '0011_localdistribution'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='localdistribution',
            name='plant',
        ),
        migrations.CreateModel(
            name='Plant_LocalDistribution',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('localID', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='PlantWebApp.localdistribution')),
                ('plantID', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='PlantWebApp.plant')),
            ],
        ),
        migrations.AddField(
            model_name='plant',
            name='localDistribution',
            field=models.ManyToManyField(blank=True, null=True, through='PlantWebApp.Plant_LocalDistribution', to='PlantWebApp.LocalDistribution'),
        ),
    ]