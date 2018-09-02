# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth import get_user_model
from django.db import migrations


def add_data(apps, schema):
    User = get_user_model()
    User.objects.create_superuser('admin', 'admin@example.com', 'admin')

    ExampleModel = apps.get_model('tests', "ExampleModel")
    for i in range(10):
        ExampleModel.objects.create(title="example {}".format(i))


class Migration(migrations.Migration):
    dependencies = [
        ('tests', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(add_data)
    ]
