# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-12-24 21:42
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('search_engine', '0009_auto_20171224_1556'),
    ]

    operations = [
        migrations.AddField(
            model_name='queryrequest',
            name='page',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
