from django import forms
from ..models import UserProfile


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
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            #'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

