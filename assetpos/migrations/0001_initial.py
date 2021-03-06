# Generated by Django 2.1.5 on 2019-04-29 15:25

import django.contrib.gis.db.models.fields
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('raster', '0001_initial'),
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
                ('location', django.contrib.gis.db.models.fields.PointField(srid=3857)),
                ('orientation', models.FloatField()),
                ('asset', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='assetpos.Asset')),
            ],
        ),
        migrations.CreateModel(
            name='AssetType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.TextField()),
                ('placement_areas', django.contrib.gis.db.models.fields.MultiPolygonField(null=True, srid=3857)),
            ],
        ),
        migrations.CreateModel(
            name='Attribute',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value', models.FloatField()),
                ('asset', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='attributes', to='assetpos.Asset')),
            ],
        ),
        migrations.CreateModel(
            name='Property',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('identifier', models.TextField()),
                ('asset_type', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='assetpos.AssetType')),
            ],
        ),
        migrations.AddField(
            model_name='attribute',
            name='property',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='assetpos.Property'),
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
        migrations.AddField(
            model_name='asset',
            name='asset_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='assetpos.AssetType'),
        ),
    ]
