from django.db import models
from .user_profile import UserProfile
from .question import Question


class QuestionMessage(models.Model):
    """Повідомлення в діалозі"""
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='messages')
    author = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
        verbose_name = "Повідомлення"
        verbose_name_plural = "Повідомлення"
    
    def __str__(self):
        return f"{self.author.username} — {self.created_at:%d.%m.%Y %H:%M}"