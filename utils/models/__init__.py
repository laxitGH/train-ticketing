from django.db import models
from django.utils import timezone


class ModelUtils:

    class BaseModel(models.Model):
        id = models.BigAutoField(primary_key=True)
        deleted = models.BooleanField(default=False)
        created_at = models.DateTimeField(null=False, blank=False)
        updated_at = models.DateTimeField(null=False, blank=False)
        metadata = models.JSONField(default=dict)

        class NonDeletedManager(models.Manager):
            def get_queryset(self):
                return super().get_queryset().filter(deleted=False)

        all_objects = models.Manager()
        objects = NonDeletedManager()

        def save(self, *args, **kwargs):
            if not self.created_at:
                self.created_at = timezone.now()
            self.updated_at = timezone.now()
            super().save(*args, **kwargs)

        class Meta:
            abstract = True
