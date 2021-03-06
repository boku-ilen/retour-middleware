# Generated by Django 2.1.5 on 2019-04-29 15:25

import django.contrib.gis.db.models.fields
import django.contrib.postgres.fields
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('location', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='DigitalHeightModel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('point', django.contrib.gis.db.models.fields.PointField(srid=3857)),
                ('height', models.FloatField()),
                ('resolution', models.FloatField()),
            ],
        ),
        migrations.CreateModel(
            name='Tile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('lod', models.IntegerField()),
                ('x', models.IntegerField()),
                ('y', models.IntegerField()),
                ('heightmap', django.contrib.postgres.fields.ArrayField(base_field=django.contrib.postgres.fields.ArrayField(base_field=models.FloatField(), size=256), blank=True, null=True, size=256)),
                ('watersplatmap', django.contrib.postgres.fields.ArrayField(base_field=django.contrib.postgres.fields.ArrayField(base_field=models.BooleanField(), size=256), blank=True, null=True, size=256)),
                ('parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='children', to='raster.Tile')),
                ('scenario', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='location.Scenario')),
            ],
        ),
        migrations.AddField(
            model_name='digitalheightmodel',
            name='tile',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='raster.Tile'),
        ),
    ]
