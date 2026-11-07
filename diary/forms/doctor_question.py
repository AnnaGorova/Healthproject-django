from django import forms
from ..models import Question   
from ..models import UserProfile


class DoctorQuestionForm(forms.ModelForm):
    doctor = forms.ModelChoiceField(
        queryset=UserProfile.objects.filter(
            role='doctor',
            user__is_active=True,
        ),
        label="Лікар",
        empty_label="-- Оберіть лікаря --",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = Question
        fields = ['doctor', 'phone', 'question']
        widgets = {
            'phone': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': '+380...',
                'type': 'tel',
                'pattern': r'^\+380[0-9]{9}$',
                'maxlength': '13',
                'title': 'Введіть +380 та 9 цифр, без пробілів',
            }),
            'question': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 6, 
                'placeholder': 'Опишіть ваше питання...'
            }),
        }

        
    def clean_question(self):
       
        question = self.cleaned_data.get('question')

        
        if '???' in question:
            raise forms.ValidationError('Можна будь-ласка без трьох знаків питання?')

        if len(question) < 10:
            raise forms.ValidationError('Питання має містити не менше 10 символів')

        return question
