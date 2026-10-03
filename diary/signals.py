from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.urls import reverse
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string

from .models import UserProfile, DoctorProfile


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Автоматично створює UserProfile при створенні User"""
    if created:
        # Роль — з форми (якщо є) або за замовчуванням
        role = getattr(instance, '_pending_role', None)
        
        if role is None:
            if instance.is_superuser or instance.is_staff:
                role = 'admin'
            else:
                role = 'patient'
        
        # Формуємо ПІБ
        full_name = f"{instance.last_name} {instance.first_name}".strip()
        if not full_name:
            full_name = instance.username
        
        profile = UserProfile.objects.create(
            user=instance,
            username=full_name,
            email=instance.email,
            role=role,
        )
        
        # Для лікаря — створити DoctorProfile
        if role == 'doctor':
            DoctorProfile.objects.create(
                user=profile,
                specialty='Терапевт',
                year_of_experience=0,
                phone='',
            )


@receiver(post_save, sender=User)
def send_password_setup_email(sender, instance, created, **kwargs):
    """Надсилає лист при створенні User без пароля"""
    if created and not instance.is_staff and not instance.has_usable_password():
        token = default_token_generator.make_token(instance)
        uid = urlsafe_base64_encode(force_bytes(instance.pk))
        
        message = render_to_string('diary/registration/password_reset_email.html', {
            'user': instance,
            'uid': uid,
            'token': token,
            'protocol': settings.PROTOCOL,
            'domain': settings.DOMAIN,
        })
        
        send_mail(
            subject='Встановлення пароля для Smart Health Bridge',
            message='',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[instance.email],
            html_message=message,
            fail_silently=False,
        )