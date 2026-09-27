from django import forms
from ..models import UserProfile
import re

class UserProfileForm(forms.ModelForm):
    phone = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+380XXXXXXXXX'
        }),
        label='Телефон',
        help_text='Формат: +380XXXXXXXXX'
    )



    class Meta:
        model = UserProfile
        fields = ['username', 'phone', 'gender', 'date_of_birth']
        
        labels = {
            'username': 'ПІБ',
            'phone': 'Телефон',
            'gender': 'Стать',
            'date_of_birth': 'Дата народження',
        }
        
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Прізвище Ім\'я По батькові'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+380XXXXXXXXX',
                'type': 'tel',
                'pattern': r'^\+?[\d\s\-\(\)]{10,20}$',
                'title': 'Введіть коректний номер телефону'
            }),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={
                'class': 'form-control', 
                'type': 'date'
            }),
        }
        
        help_texts = {
            'phone': 'Формат: +380XXXXXXXXX',
        }


    def clean_username(self):
        value = self.cleaned_data.get('username', '')
        # прибираємо пробіли з країв і схлопуємо будь-яку кількість пробілів підряд в один
        value = re.sub(r'\s+', ' ', value).strip()
        return value
