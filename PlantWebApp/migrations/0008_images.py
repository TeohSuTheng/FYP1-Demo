# Generated by Django 3.2.3 on 2021-11-05 07:44

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('PlantWebApp', '0007_auto_20211104_0037'),
    ]

    operations = [
        migrations.CreateModel(
            name='Images',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(blank=True, default='default.jpeg', upload_to='plantImg/')),
                ('plant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='PlantWebApp.plant')),
            ],
        ),
    ]