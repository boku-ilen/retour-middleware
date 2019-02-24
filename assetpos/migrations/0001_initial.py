# Generated by Django 2.1.7 on 2019-02-24 18:00

import django.contrib.gis.db.models.fields
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('raster', '__first__'),
    ]

    operations = [
        migrations.CreateModel(
            name='Asset',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='AssetPositions',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('location', django.contrib.gis.db.models.fields.PointField(srid=4326)),
                ('orientation', models.FloatField()),
                ('asset', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='assetpos.Asset')),
            ],
        ),
        migrations.CreateModel(
            name='AssetType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.TextField()),
            ],
        ),
        migrations.AddField(
            model_name='assetpositions',
            name='asset_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='assetpos.AssetType'),
        ),
        migrations.AddField(
            model_name='assetpositions',
            name='tile',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='raster.Tile'),
        ),
    ]
