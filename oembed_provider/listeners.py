from django.db.models.signals import post_save

from oembed import models
from oembed import site


def provider_site_invalidate(sender, instance, created, **kwargs):
    site.invalidate_providers()


def start_listening():
    post_save.connect(provider_site_invalidate, sender=models.StoredProvider)
