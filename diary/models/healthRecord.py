from django.db import models
from .user_profile import UserProfile


class HealthRecord(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='records')
    date = models.DateTimeField(auto_now_add=True)
    well_being = models.CharField(max_length=50, blank=True)
    temperature = models.FloatField(default=36.6)
    pressure = models.CharField(max_length=20, blank=True)
    complaints = models.TextField(blank=True)
    comment = models.TextField(blank=True)
    medicines = models.ManyToManyField('Medicine', blank=True, related_name='records')


    def __str__(self):
       return f"#{self.id}: {self.user.username} - {self.date:%d.%m.%Y}"





