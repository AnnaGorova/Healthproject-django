from django.db import models
from django.utils import timezone        
from datetime import timedelta   
from .user_profile import UserProfile
from .schedule import Schedule


class Appointment(models.Model):
    STATUS_CHOICES = [
        ('scheduled', 'Активний'),
        ('completed', 'Завершений'),
        ('cancelled', 'Скасовано'),
    ]
    
    patient = models.ForeignKey(
        UserProfile, 
        on_delete=models.CASCADE, 
        related_name='appointments',
        limit_choices_to={'role': 'patient'}
    )
    doctor = models.ForeignKey(
        UserProfile, 
        on_delete=models.CASCADE, 
        related_name='doctor_appointments',
        limit_choices_to={'role': 'doctor'}
    )
    date = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    complaints = models.TextField(blank=True, verbose_name="Скарги")
    comment = models.TextField(blank=True, verbose_name="Коментар")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['date']
        verbose_name = "Прийом"
        verbose_name_plural = "Прийоми"
        
    
    def __str__(self):
        return f"{self.patient.username} → {self.doctor.username} ({self.date:%d.%m.%Y %H:%M})"

    @property
    def duration_minutes(self):
        """Тривалість прийому — з розкладу лікаря на цю дату, або 30 хв за замовчуванням"""
        schedule = Schedule.objects.filter(
            doctor=self.doctor,
            date=self.date.date(),
            is_day_off=False
        ).first()
        return schedule.slot_duration if schedule else 30


    @property
    def can_cancel(self):
        """Чи можна скасувати запис (за 24 години до прийому)"""
        if self.status != 'scheduled':
            return False
        return self.date - timezone.now() >= timedelta(hours=24)

    @property
    def is_overdue(self):
        """Прийом уже завершився (з урахуванням реальної тривалості), а висновок не створено"""
        end_time = self.date + timedelta(minutes=self.duration_minutes)
        return self.status == 'scheduled' and end_time < timezone.now()