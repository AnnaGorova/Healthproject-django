from django.db import models
from .user_profile import UserProfile
from django.core.validators import RegexValidator


class DoctorProfile(models.Model):
    user = models.OneToOneField(
        UserProfile,
        on_delete=models.CASCADE,
        related_name='doctor_profile',
        limit_choices_to={'role' : 'doctor'} 
    )

    specialty = models.CharField(max_length=100, verbose_name="Спеціальність")
    year_of_experience = models.PositiveIntegerField (default=0 , verbose_name="Стаж роботи")
    phone = models.CharField(
            max_length=20, 
            blank=True,
            validators=[
                RegexValidator(
                    regex=r'^\+?[\d\s\-\(\)]{10,20}$',
                    message="Введіть коректний номер телефону"
                )
            ]
        )

    def __str__(self):
        return f"Лікар: {self.user.username} - {self.specialty}"