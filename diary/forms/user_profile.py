from django import forms
from ..models import UserProfile
import re

class UserProfileForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.role in ('patient', 'admin', 'doctor'):
            self.fields['date_of_birth'].widget = forms.DateInput(
                format='%d.%m.%Y',
                attrs={
                    'class': 'form-control',
                    'placeholder': 'ДД.ММ.РРРР',
                    'inputmode': 'numeric',
                    'maxlength': '10',
                },
            )
            self.fields['date_of_birth'].input_formats = ['%d.%m.%Y', '%Y-%m-%d']

    phone = forms.CharField(
        required=False,
        max_length=13,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+380XXXXXXXXX',
            'type': 'tel',
            'pattern': r'^\+380[0-9]{9}$',
            'title': 'Введіть +380 та 9 цифр, без пробілів',
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
                'pattern': r'^\+380[0-9]{9}$',
                'maxlength': '13',
                'title': 'Введіть +380 та 9 цифр, без пробілів'
            }),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'date_of_birth': forms.DateInput(format='%Y-%m-%d', attrs={
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
