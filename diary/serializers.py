from rest_framework import serializers
from .models import HealthRecord



class HealthRecordSerializer(serializers.ModelSerializer): 
    user_name = serializers.CharField(source='user.username', read_only=True)
   
    class Meta:
        model = HealthRecord
        fields = [
            'id', 
            'user', 
            'user_name', 
            'date',
            # === САМОПОЧУТТЯ ===
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
            
            'is_active',
        ]