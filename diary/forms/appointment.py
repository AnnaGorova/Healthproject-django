from django import forms
from ..models import Appointment, UserProfile


class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['doctor', 'date', 'complaints']
        
        labels = {
            'doctor': 'Лікар',
            'date': 'Дата та час',
            'complaints': 'Скарги',
        }
        
        widgets = {
            'doctor': forms.Select(attrs={'class': 'form-control'}),
            'date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'complaints': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
       
        self.fields['doctor'].queryset = UserProfile.objects.filter(role='doctor')