from django.db import models
from .user_profile import UserProfile
from .appointment import Appointment



class MedicalConclusion(models.Model):
    """Висновок лікаря (Форма № 028/о)"""
    appointment = models.OneToOneField(
        Appointment,
        on_delete=models.CASCADE,
        related_name='conclusion',
        verbose_name="Прийом"
    )
    doctor = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name='conclusions',
        limit_choices_to={'role': 'doctor'},
        verbose_name="Лікар"
    )
    patient = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name='patient_conclusions',
        limit_choices_to={'role': 'patient'},
        verbose_name="Пацієнт"
    )
    icd10 = models.ForeignKey(
        'diary.ICD10Code',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='conclusions',
        verbose_name="Код МКХ-10"
    )
    
    diagnosis = models.TextField(verbose_name="Діагноз")
    prescriptions = models.TextField(verbose_name="Призначення")
    recommendations = models.TextField(verbose_name="Рекомендації")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата створення")
    
    class Meta:
        ordering = ['created_at']
        verbose_name = "Висновок"
        verbose_name_plural = "Висновки"
    
    def __str__(self):
        return f"{self.patient.username} — {self.doctor.username} ({self.created_at:%d.%m.%Y})"