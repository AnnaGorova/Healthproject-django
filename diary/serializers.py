from rest_framework import serializers
from.models import HealthRecord, Medicine

class MedicineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Medicine
        fields = ['id', 'name', 'dosage', 'purpose']


class HealthRecordSerializer(serializers.ModelSerializer): 
    user_name = serializers.CharField(source='user.username', read_only=True)
    medicines = MedicineSerializer(many=True, read_only=True)

    class Meta:
        model = HealthRecord
        fields = [
            'id', 'user', 'user_name', 'date', 'well_being',
            'temperature', 'pressure', 'complaints', 'comment', 'medicines'
        ]   
