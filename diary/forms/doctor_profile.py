from django import forms
from ..models import DoctorProfile


class DoctorProfileForm(forms.ModelForm):
    
    class Meta:
        model = DoctorProfile
        fields = ['specialty', 'year_of_experience', 'phone']
        widgets = {
            'specialty': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Наприклад: Терапевт'
            }),
            'year_of_experience': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'placeholder': '0'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+380XXXXXXXXX',
                'type': 'tel',                            # ← HTML5
                'pattern': r'^\+?[\d\s\-\(\)]{10,20}$',   # ← HTML5 pattern
                'title': 'Введіть коректний номер телефону'
            }),
        }
        labels = {
            'specialty': 'Спеціалізація',
            'year_of_experience': 'Стаж роботи (років)',
            'phone': 'Робочий телефон',
        }
        help_texts = {
            'phone': 'Формат: +380XXXXXXXXX',
        }