from django.contrib import admin
from diary.models import UserProfile, HealthRecord, DoctorProfile, Question
from .models import Schedule, Appointment

# Register your models here.


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = [
        'id', 
        'username', 
        'email', 
        'role', 
        'phone',           
        'gender',          
        'date_of_birth',   
        'doctor'
    ]
    list_filter = [
        'role', 
        'gender',          
        'doctor'
    ]
    search_fields = [
        'username', 
        'email', 
        'phone'            
    ]
    raw_id_fields = ['doctor']
    
    fieldsets = (
        ('Основна інформація', {
            'fields': ('user', 'username', 'email', 'role')
        }),
        ('Особиста інформація', {
            'fields': ('phone', 'gender', 'date_of_birth')
        }),
        ('Зв\'язки', {
            'fields': ('doctor',)
        }),
    )




@admin.register(HealthRecord)
class HealthRecordAdmin(admin.ModelAdmin):
    list_display = [
        'id', 
        'user', 
        'complaints', 
        'date', 
        'well_being', 
        'temperature', 
        'heart_rate',      
        'pressure_systolic',  
        'pressure_diastolic',
        'spo2',       
        'mood',            
        'sleep_hours',     
        'steps',           
        'is_active'
        
        ]
    list_filter = [
        'well_being', 
        'mood', 
        'is_active',
        'date', 
        'energy_level',    
        'pain_level'       
        ]
    search_fields = ['user__username', 'complaints']
  
    readonly_fields = ['date']

    fieldsets = (
        ('Основна інформація', {
            'fields': ('user', 'date', 'is_active')
        }),
        ('Самопочуття', {
            'fields': ('well_being', 'mood')
        }),
        ('Показники здоров\'я', {
            'fields': ('heart_rate', 'pressure_systolic', 'pressure_diastolic', 
                       'temperature', 'spo2', 'blood_sugar', 'weight')
        }),
        ('Емоційний стан', {
            'fields': ('energy_level', 'pain_level')
        }),
        ('Спосіб життя', {
            'fields': ('water_intake', 'calories', 'steps', 'sleep_hours')
        }),
        ('Додатково', {
            'fields': ( 'complaints', 'comment')
        }),
       
    )




@admin.register(DoctorProfile)
class DoctorProfileAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'specialty', 'year_of_experience', 'phone']
    list_filter = ['specialty', 'year_of_experience']
    search_fields = ['user__username', 'specialty', 'phone']
    raw_id_fields = ['user']


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['patient', 'phone', 'created_at', 'is_answered']
    search_fields = ['patient__username', 'phone']



@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ['doctor', 'date', 'start_time', 'end_time', 'slot_duration']
    list_filter = ['doctor', 'date']
    search_fields = ['doctor__username']

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ['id', 'patient', 'doctor', 'date', 'status']
    list_filter = ['status', 'date']
    search_fields = ['patient__username', 'doctor__username']
    raw_id_fields = ['patient', 'doctor']