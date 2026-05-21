from django.contrib import admin
from diary.models import UserProfile, Medicine, HealthRecord, DoctorProfile, Question

# Register your models here.


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['id', 'username', 'email', 'role', 'doctor']
    list_filter = ['role', 'doctor']
    search_fields = ['username', 'email']
    raw_id_fields = ['doctor']

@admin.register(Medicine)
class MedicineAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'dosage', 'purpose']
    list_filter = ['purpose']
    search_fields = ['name', 'purpose']


@admin.register(HealthRecord)
class HealthRecordAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'complaints', 'date', 'well_being', 'temperature', 'is_active']
    list_filter = ['well_being', 'is_active', 'date']
    search_fields = ['user__username', 'complaints']
    filter_horizontal = ['medicines']
    readonly_fields = ['date']




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
