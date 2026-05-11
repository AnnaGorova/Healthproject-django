from django.db import models



class UserProfile(models.Model):
    username = models.CharField(max_length=100)
    email = models.EmailField()
    role = models.CharField(max_length=20, choices=[
        ('patient', 'Пацієнт'),
        ('doctor', 'Лікар'),
        ('admin', 'Адміністратор'),
    ], default='patient')



    doctor = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL,
        null=True, 
        blank=True,
        limit_choices_to={'role':'doctor'}, 
        related_name='patients'
        )

    def __str__(self):
        return f"{self.username}  {self.email}  {self.role}" 