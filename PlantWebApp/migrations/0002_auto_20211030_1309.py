# Generated by Django 3.2.3 on 2021-10-30 05:09

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('PlantWebApp', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Role',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role_name', models.CharField(max_length=30)),
            ],
        ),
        migrations.AlterField(
            model_name='profile',
            name='role',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='PlantWebApp.role'),
        ),
    ]
