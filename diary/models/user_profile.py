from django.db import models



class UserProfile(models.Model):
    username = models.CharField(max_length=100)
    email = models.EmailField()
    role = models.CharField(max_length=20, choices=[
        ('patient', 'Пацієнт'),
        ('doctor', 'Лікар'),
        ('admin', 'Адміністратор'),
    ], default='patient')

    def __str__(self):
        return f"{self.username}  {self.email}  {self.role}" 