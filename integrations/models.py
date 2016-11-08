from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models


class Integration(models.Model):
    name = models.CharField(max_length=250)


class IntegrationConfig(models.Model):
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

    # Generic Foreign key
    content_type = models.ForeignKey(ContentType, related_name="content_type_integrations")
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    # Numeric key related to the integration
    key = models.PositiveIntegerField()
    integration = models.ForeignKey(Integration)


def get_integration_id(object_instance):
    content_type = ContentType.objects.get_for_model(object_instance)
    integration_object = IntegrationConfig.objects.get(
        object_id=object_instance.pk,
        content_type=content_type)
    return integration_object.key