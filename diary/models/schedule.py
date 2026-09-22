from django.db import models
from .user_profile import UserProfile


class Schedule(models.Model):
    """Розклад лікаря на конкретну дату"""
    doctor = models.ForeignKey(
        UserProfile, 
        on_delete=models.CASCADE, 
        related_name='schedules',
        limit_choices_to={'role': 'doctor'}
    )
    date = models.DateField(verbose_name="Дата")
    is_day_off = models.BooleanField(default=False, verbose_name="Вихідний") 
    start_time = models.TimeField(verbose_name="Початок", null=True, blank=True)  
    end_time = models.TimeField(verbose_name="Кінець", null=True, blank=True)    
    slot_duration = models.IntegerField(default=30, verbose_name="Тривалість прийому (хв)")
    
    class Meta:
        ordering = ['date', 'start_time']
        verbose_name = "Розклад"
        verbose_name_plural = "Розклади"
        unique_together = ['doctor', 'date', 'start_time']
    
    def __str__(self):
        if self.is_day_off:
            return f"{self.doctor.username} — {self.date:%d.%m.%Y} (вихідний)"
        return f"{self.doctor.username} — {self.date:%d.%m.%Y} ({self.start_time}-{self.end_time})"