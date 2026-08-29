from django.db import models
from .user_profile import UserProfile


class HealthRecord(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='records')
    date = models.DateTimeField(auto_now_add=True)
    well_being = models.CharField(max_length=50, blank=True)
    temperature = models.FloatField(default=36.6)
    pressure = models.CharField(max_length=20, blank=True)
    heart_rate = models.IntegerField(
        null=True, 
        blank=True, 
        help_text="Пульс (удари за хвилину)"
    )
    blood_sugar = models.FloatField(
        null=True, 
        blank=True, 
        help_text="Рівень цукру в крові (ммоль/л)"
    )

    weight = models.FloatField(
        null=True, 
        blank=True, 
        help_text="Вага (кг)"
    )
    sleep_hours = models.FloatField(
        null=True, 
        blank=True, 
        help_text="Сон за ніч (години)"
    )
    steps = models.IntegerField(
        null=True, 
        blank=True, 
        help_text="Кількість кроків за день"
    )
    complaints = models.TextField(blank=True)
    mood = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        choices=[
            ('great', 'Чудово'),
            ('good', 'Добре'),
            ('okay', 'Нормально'),
            ('bad', 'Погано'),
            ('terrible', 'Жахливо')
        ],
        help_text="Настрій"
    )
    energy_level = models.IntegerField(
        null=True,
        blank=True,
        choices=[(i, str(i)) for i in range(1, 11)],
        help_text="Рівень енергії (1-10)"
    )
    pain_level = models.IntegerField(
        null=True,
        blank=True,
        choices=[(i, str(i)) for i in range(0, 11)],
        help_text="Рівень болю (0-10)"
    )
    water_intake = models.IntegerField(
        null=True,
        blank=True,
        help_text="Вода (мл за день)"
    )
    calories = models.IntegerField(
        null=True,
        blank=True,
        help_text="Калорії за день"
    )
    comment = models.TextField(blank=True)
    medicines = models.ManyToManyField('Medicine', blank=True, related_name='records')
    is_active = models.BooleanField(default=True)



    def __str__(self):
       return f"#{self.id}: {self.user.username} - {self.date:%d.%m.%Y}"

    class Meta:
        ordering = ['-date']  
        verbose_name = "Запис здоров'я"
        verbose_name_plural = "Записи здоров'я"



