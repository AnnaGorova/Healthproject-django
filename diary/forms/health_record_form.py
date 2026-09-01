from django import forms
from ..models import HealthRecord


class HealthRecordForm(forms.ModelForm):
       
    class Meta:
        model = HealthRecord
        fields = [
            'well_being', 
            'temperature', 
            'pressure',
            'heart_rate', 
            'spo2',
            'blood_sugar',       
            'weight',            
            'sleep_hours',       
            'steps',             
            'mood',              
            'energy_level',      
            'pain_level',        
            'water_intake',      
            'calories',                      
            'complaints', 
            'comment', 
            'medicines'
            ]
        

        labels = {
            'well_being': 'Самопочуття',
            'temperature': 'Температура (°C)',
            'pressure': 'Артеріальний тиск',
            'heart_rate': 'Пульс (удари/хв)',
            'spo2': 'Сатурація (SpO2) %',
            'blood_sugar': 'Рівень цукру (ммоль/л)',
            'weight': 'Вага (кг)',
            'sleep_hours': 'Сон (години)',
            'steps': 'Кроки за день',
            'mood': 'Настрій',
            'energy_level': 'Рівень енергії (1-10)',
            'pain_level': 'Рівень болю (0-10)',
            'water_intake': 'Вода (мл)',
            'calories': 'Калорії за день',       
            'complaints': 'Скарги',
            'comment': 'Коментар',
            'medicines': 'Ліки',
        }