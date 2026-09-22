from django.db import models
from .user_profile import UserProfile


class Question(models.Model):
    STATUS_CHOICES = [
        ('new', 'Нове'),
        ('answered', 'Відповідь надано'),
        ('closed', 'Закрито'),
    ]
    
    patient = models.ForeignKey(
        UserProfile, 
        on_delete=models.CASCADE, 
        related_name='questions'
    )
    doctor = models.ForeignKey(
        UserProfile, 
        on_delete=models.CASCADE,
        related_name='doctor_questions',
        limit_choices_to={'role': 'doctor'},
        verbose_name="Лікар"
    )
    phone = models.CharField(max_length=15)
    question = models.TextField()
    answer = models.TextField(blank=True, verbose_name="Відповідь лікаря")
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='new'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    answered_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Питання"
        verbose_name_plural = "Питання"
    
    def __str__(self):
        return f"{self.patient.username} - {self.created_at.strftime('%d.%m.%Y')}"