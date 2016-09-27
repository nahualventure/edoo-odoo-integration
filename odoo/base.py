from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic

CONTRACTS = {

}

class OdooProfile(models.Model):
    content_type = models.ForeignKey(ContentType, related_name="content_type_timelines")
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey('content_type', 'object_id')
    event_type = models.CharField(max_length=250, default="created")
