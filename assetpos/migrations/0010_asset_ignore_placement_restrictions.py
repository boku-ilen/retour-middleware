# Generated by Django 2.2.4 on 2019-09-25 17:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('assetpos', '0009_auto_20190907_2222'),
    ]

    operations = [
        migrations.AddField(
            model_name='asset',
            name='ignore_placement_restrictions',
            field=models.BooleanField(default=False),
        ),
    ]
