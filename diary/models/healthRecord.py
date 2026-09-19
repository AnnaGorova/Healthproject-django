from django.db import models
from .user_profile import UserProfile
from django.core.validators import MinValueValidator, MaxValueValidator


class HealthRecord(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='records')
    date = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True) 

    well_being = models.CharField(max_length=50, blank=True)
    
  
    temperature = models.FloatField(
        null=True,           
        blank=True,          
        validators=[
            MinValueValidator(30.0, message="Температура має бути від 30.0 до 45.0 °C"),
            MaxValueValidator(45.0, message="Температура має бути від 30.0 до 45.0 °C")
        ],
        help_text="Температура (°C)"
    )
    
   
    heart_rate = models.IntegerField(
        null=True, 
        blank=True,
        validators=[
            MinValueValidator(30, message="Пульс має бути від 30 до 250 уд/хв"),
            MaxValueValidator(250, message="Пульс має бути від 30 до 250 уд/хв")
        ],
        help_text="Пульс (уд/хв)"
    )
    

    spo2 = models.IntegerField(
        null=True, 
        blank=True,
        validators=[
            MinValueValidator(50, message="Сатурація має бути від 50 до 100%"),
            MaxValueValidator(100, message="Сатурація має бути від 50 до 100%")
        ],
        help_text="Сатурація (SpO2) %"
    )
    
    
    pressure_systolic = models.IntegerField(
        null=True, 
        blank=True,
        validators=[
            MinValueValidator(60, message="Систолічний тиск має бути від 60 до 250 мм рт.ст."),
            MaxValueValidator(250, message="Систолічний тиск має бути від 60 до 250 мм рт.ст.")
        ],
        help_text="Артеріальний тиск (систолічний) мм рт.ст."
    )
    
   
    pressure_diastolic = models.IntegerField(
        null=True, 
        blank=True,
        validators=[
            MinValueValidator(40, message="Діастолічний тиск має бути від 40 до 150 мм рт.ст."),
            MaxValueValidator(150, message="Діастолічний тиск має бути від 40 до 150 мм рт.ст.")
        ],
        help_text="Артеріальний тиск (діастолічний) мм рт.ст."
    )
    
  
    blood_sugar = models.FloatField(
        null=True, 
        blank=True,
        validators=[
            MinValueValidator(1.0, message="Рівень цукру має бути від 1.0 до 30.0 ммоль/л"),
            MaxValueValidator(30.0, message="Рівень цукру має бути від 1.0 до 30.0 ммоль/л")
        ],
        help_text="Рівень цукру (ммоль/л)"
    )

   
    weight = models.FloatField(
        null=True, 
        blank=True,
        validators=[
            MinValueValidator(1.0, message="Вага має бути від 1.0 до 300.0 кг"),
            MaxValueValidator(300.0, message="Вага має бути від 1.0 до 300.0 кг")
        ],
        help_text="Вага (кг)"
    )
    
  
    sleep_hours = models.FloatField(
        null=True, 
        blank=True,
        validators=[
            MinValueValidator(0.0, message="Сон має бути від 0 до 24 годин"),
            MaxValueValidator(24.0, message="Сон має бути від 0 до 24 годин")
        ],
        help_text="Сон за ніч (години)"
    )
    
    
    steps = models.IntegerField(
        null=True, 
        blank=True,
        validators=[
            MinValueValidator(0, message="Кроки мають бути від 0 до 100000"),
            MaxValueValidator(100000, message="Кроки мають бути від 0 до 100000")
        ],
        help_text="Кількість кроків за день"
    )
    
    
    water_intake = models.IntegerField(
        null=True, 
        blank=True,
        validators=[
            MinValueValidator(0, message="Вода має бути від 0 до 10000 мл"),
            MaxValueValidator(10000, message="Вода має бути від 0 до 10000 мл")
        ],
        help_text="Вода (мл за день)"
    )
    
    calories = models.IntegerField(
        null=True, 
        blank=True,
        validators=[
            MinValueValidator(0, message="Калорії мають бути від 0 до 10000 ккал"),
            MaxValueValidator(10000, message="Калорії мають бути від 0 до 10000 ккал")
        ],
        help_text="Калорії за день"
    )
    
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
    
    
    pain_level = models.IntegerField(
        null=True,
        blank=True,
        choices=[(i, str(i)) for i in range(0, 11)],
        help_text="Рівень болю (0-10)"
    )
    
    
    energy_level = models.IntegerField(
        null=True,
        blank=True,
        choices=[(i, str(i)) for i in range(1, 11)],
        help_text="Рівень енергії (1-10)"
    )

    
    complaints = models.TextField(blank=True)
    comment = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"#{self.id}: {self.user.username} - {self.date:%d.%m.%Y}"

    class Meta:
        ordering = ['-date']  
        verbose_name = "Запис здоров'я"
        verbose_name_plural = "Записи здоров'я"