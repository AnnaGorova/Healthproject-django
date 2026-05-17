from django import forms
from ..models import HealthRecord


class HealthRecordForm(forms.ModelForm):
       
    class Meta:
        model = HealthRecord
        fields = ['well_being', 'temperature', 'pressure', 
                  'complaints', 'comment', 'medicines']
        

        labels = {
            'well_being': 'Самопочуття',
            'temperature': 'Температура (°C)',
            'pressure': 'Артеріальний тиск',
            'complaints': 'Скарги',
            'comment': 'Коментар',
            'medicines': 'Ліки',
        }