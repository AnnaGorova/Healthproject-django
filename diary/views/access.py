from ..models import UserProfile
from ..models import Appointment
from django.db.models import Q


def is_admin_or_superuser(user):
    """Перевірка: адмін або супер_адмін"""
    if user.is_superuser:
        return True
    if hasattr(user, 'userprofile') and user.userprofile.role == 'admin':
        return True
    return False


def get_accessible_patients(doctor_profile):
    """
    Пацієнти, доступні лікарю:
    1. Закріплені (patient.doctor == лікар)
    2. Прийоми, які НЕ скасовані (scheduled АБО completed)
    
    Скасований прийом (cancelled) — НЕ дає доступу.
    """
    return UserProfile.objects.filter(
        role='patient'
    ).filter(
        Q(doctor=doctor_profile) |
        Q(appointments__doctor=doctor_profile,
          appointments__status__in=['scheduled', 'completed'])
    ).distinct()


def doctor_can_access_patient(doctor_profile, patient_profile):
    """Перевірка доступу лікаря до конкретного пацієнта"""
    if not patient_profile or patient_profile.role != 'patient':
        return False
    
    if patient_profile.doctor == doctor_profile:
        return True
    
    return Appointment.objects.filter(
        doctor=doctor_profile,
        patient=patient_profile,
        status__in=['scheduled', 'completed']
    ).exists()


def is_doctor(user):
    return user.is_authenticated and user.userprofile.role == 'doctor'


def is_admin(user):
  return user.is_authenticated and user.userprofile.role == 'admin'
