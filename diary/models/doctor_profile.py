from django.db import models
from .user_profile import UserProfile


class DoctorProfile(models.Model):
    user = models.OneToOneField(
        UserProfile,
        on_delete=models.CASCADE,
        related_name='doctor_profile',
        limit_choices_to={'role' : 'doctor'} 
    )

    specialty = models.CharField(max_length=100, verbose_name="Спеціальність")
    year_of_experience = models.PositiveIntegerField (default=0 , verbose_name="Стаж роботи")
    phone = models.CharField(max_length=15, blank=True, verbose_name="Телефон")


    def __str__(self):
        return f"Лікар: {self.user.username} - {self.specialty}"