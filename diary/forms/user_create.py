from django import forms
from django.contrib.auth.models import User


class UserCreateForm(forms.ModelForm):
    """Форма створення User без пароля (для адмінки)"""
    
    ROLE_CHOICES = [
        ('patient', 'Пацієнт'),
        ('doctor', 'Лікар'),
        ('admin', 'Адміністратор'),
    ]
    
    role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        label='Роль',
        initial='patient',
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text='Оберіть роль для нового користувача'
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'ivanov_ivan (латиниця, без пробілів)'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'ivanov@example.com'
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Іван'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Іванов'
            }),
        }
        labels = {
            'username': 'Логін (латиниця, без пробілів)',
            'email': 'Email',
            'first_name': "Ім'я",
            'last_name': 'Прізвище',
        }
        help_texts = {
            'username': 'Технічний логін — не показується пацієнтам',
        }
    
    def save(self, commit=True):
        """Зберігає User без пароля + запам'ятовує роль"""
        user = super().save(commit=False)
        user.set_unusable_password()
        # Запам'ятати роль у тимчасовому атрибуті
        user._pending_role = self.cleaned_data.get('role', 'patient')
        if commit:
            user.save()
        return user