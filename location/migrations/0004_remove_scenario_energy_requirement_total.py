# Generated by Django 2.2.1 on 2019-09-07 22:22

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('location', '0003_auto_20190904_2155'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='scenario',
            name='energy_requirement_total',
        ),
    ]
