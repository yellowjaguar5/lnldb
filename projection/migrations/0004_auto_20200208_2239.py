# -*- coding: utf-8 -*-
# Generated by Django 1.11.27 on 2020-02-09 03:39
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projection', '0003_auto_20181021_2135'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pitinstance',
            name='created_on',
            field=models.DateField(),
        ),
    ]
