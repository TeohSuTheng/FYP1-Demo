# Generated by Django 3.2.3 on 2022-01-07 14:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('PlantWebApp', '0022_auto_20220107_2226'),
    ]

    operations = [
        migrations.AlterField(
            model_name='plant',
            name='extract',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='plant',
            name='oil',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='plant',
            name='powder',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='plant',
            name='voucher',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]