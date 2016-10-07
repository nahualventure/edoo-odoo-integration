from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
#from django.contrib.contenttypes import generic

class Integrations(models.Model):
    name = models.CharField(max_length=250)

class IntegrationConfiguration(models.Model):
    """
        Represent items of the current integrations

        This class stores the items of any present integration in Edoo,
        uses a Generic Foreign key to map a current Edoo model to any
        integration.

        Attributes:
            key             Identifier with the integration
            object_id       Identifier with Edoo
            content_type    Model to match with Edoo
    """

    # Numeric key that identifies the model with the
    key = models.PositiveIntegerField()
    content_type = models.ForeignKey(ContentType, related_name="content_type_timelines")
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    event_type = models.CharField(max_length=250, default="created")