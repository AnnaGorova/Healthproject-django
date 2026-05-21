from django.db import models
from .user_profile import UserProfile

class Question(models.Model):
    patient = models.ForeignKey(UserProfile, on_delete=models.CASCADE, 
                                related_name='questions')
    phone = models.CharField(max_length=15)
    question = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_answered = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.patient.username} - {self.created_at.strftime('%d.%m.%Y')}"