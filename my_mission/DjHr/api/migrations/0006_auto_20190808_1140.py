# -*- coding: utf-8 -*-
# Generated by Django 1.11.8 on 2019-08-08 03:40
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0005_rate'),
    ]

    operations = [
        migrations.AlterField(
            model_name='rate',
            name='pageinfo',
            field=models.IntegerField(default=0, help_text='公司信息最先出现的页数', verbose_name='页数信息'),
        ),
    ]
