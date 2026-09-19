from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from datetime import date

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    username = models.CharField(max_length=100)
    email = models.EmailField()
    role = models.CharField(max_length=20, choices=[
        ('patient', 'Пацієнт'),
        ('doctor', 'Лікар'),
        ('admin', 'Адміністратор'),
        ], default='patient')
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
    gender = models.CharField(
        max_length=10, 
        blank=True,
        choices=[
            ('M', 'Чоловіча'),
            ('F', 'Жіноча'),
        ]
    ) 
    date_of_birth = models.DateField(null=True, blank=True) 

    doctor = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL,
        null=True, 
        blank=True,
        limit_choices_to={'role':'doctor'}, 
        related_name='patients'
        )

    def __str__(self):
        return f"{self.username} ({self.email}) — {self.get_role_display()}"



    @property
    def age(self):
        """Обчислює вік з дати народження"""
        if self.date_of_birth:
            today = date.today()
            return today.year - self.date_of_birth.year - (
                (today.month, today.day) < 
                (self.date_of_birth.month, self.date_of_birth.day)
            )
        return None
