from django.db import models
from django.utils import timezone


class ModelUtils:

    class BaseModel(models.Model):
        id = models.BigAutoField(primary_key=True)
        deleted = models.BooleanField(default=False)
        created_at = models.DateTimeField(null=False, blank=False, auto_now_add=True)
        updated_at = models.DateTimeField(null=False, blank=False, auto_now=True)
        metadata = models.JSONField(default=dict)

        class NonDeletedManager(models.Manager):
            def generate_queryset(self):
                return super().generate_queryset().filter(deleted=False)

        all_objects = models.Manager()
        objects = NonDeletedManager()

        class Meta:
            abstract = True
