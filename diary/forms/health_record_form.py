from django import forms
from ..models import HealthRecord


class HealthRecordForm(forms.ModelForm):
       
    class Meta:
        model = HealthRecord
        fields = [
            'well_being', 
            'temperature', 
            'pressure_systolic',
            'pressure_diastolic',
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
           
            ]
        

        labels = {
            'well_being': 'Самопочуття',
            'temperature': 'Температура (°C)',
            'pressure_systolic': 'Артеріальний тиск (систолічний) мм рт.ст.',
            'pressure_diastolic': 'Артеріальний тиск (діастолічний) мм рт.ст.',
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
            
        }


    def clean(self):
        cleaned_data = super().clean()
        
        fields_to_check = [
            'well_being',
            'temperature', 
            'pressure_systolic', 
            'pressure_diastolic',
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
        ]
        
        
        has_data = False
        for field in fields_to_check:
            value = cleaned_data.get(field)
            if value:  
                has_data = True
                break
        
        if not has_data:
            raise forms.ValidationError("Заповніть хоча б один показник, щоб запис мав сенс.")
        
        return cleaned_data