from django.db import models

class TenantModel(models.Model):
    """Abstract base model for multi-tenant isolation."""
    business = models.ForeignKey(
        'businesses.Business',
        on_delete=models.CASCADE,
        related_name="%(app_label)s_%(class)s_set",
        db_index=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
