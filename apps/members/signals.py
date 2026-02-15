from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Member
from apps.communications.services import WhatsAppService

@receiver(post_save, sender=Member)
def send_welcome_whatsapp(sender, instance, created, **kwargs):
    """
    Sends a welcome WhatsApp message when a new member is created.
    """
    if created and instance.phone:
        service = WhatsAppService()
        service.send_welcome_message(instance)
