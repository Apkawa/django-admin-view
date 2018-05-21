from django.db import models


class ExampleModel(models.Model):
    title = models.CharField(max_length=100)
