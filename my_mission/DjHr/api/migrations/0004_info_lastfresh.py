# -*- coding: utf-8 -*-
# Generated by Django 1.11.8 on 2019-08-07 10:18
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0003_auto_20190807_1517'),
    ]

    operations = [
        migrations.AddField(
            model_name='info',
            name='lastFresh',
            field=models.CharField(max_length=50, null=True, verbose_name='上次刷新'),
        ),
    ]