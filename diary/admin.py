from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin   # ← ✅
from django.contrib.auth.models import User 
from diary.models import UserProfile, HealthRecord, DoctorProfile
from .models import Schedule, Appointment, Question, QuestionMessage
from .models import MedicalConclusion

# Register your models here.



from django.contrib.auth.forms import UserChangeForm, AdminPasswordChangeForm
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.urls import reverse
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.contrib import messages

from .forms.user_create import UserCreateForm


admin.site.unregister(User)

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Кастомна адмінка User — створення без пароля"""
    
    add_form = UserCreateForm              # ← кастомна форма створення
    form = UserChangeForm                  # ← стандартна форма редагування
    change_password_form = AdminPasswordChangeForm
    
    # Поля при створенні
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'first_name', 'last_name', 'role'),
        }),
    )
    
    # Дії
    actions = ['send_password_setup_email']
    
    @admin.action(description='📧 Надіслати лист для встановлення пароля')
    def send_password_setup_email(self, request, queryset):
        """Дія: відправити лист для встановлення пароля"""
        count = 0
        for user in queryset:
            if user.has_usable_password():
                messages.warning(request, f"⚠️ {user.username}: пароль вже встановлено")
                continue
            
            if not user.email:
                messages.warning(request, f"⚠️ {user.username}: немає email")
                continue
            
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            
            message = render_to_string('registration/password_reset_email.html', {
                'user': user,
                'uid': uid,
                'token': token,
                'protocol': settings.PROTOCOL,
                'domain': settings.DOMAIN,
            })
            
            send_mail(
                subject='Встановлення пароля для Smart Health Bridge',
                message='',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=message,
                fail_silently=False,
            )
            
            count += 1
            messages.success(request, f"✅ Лист надіслано: {user.username}")
        
        if count:
            self.message_user(request, f"📧 Надіслано листів: {count}")




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
        'doctor',
        'is_active_user',
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
    def is_active_user(self, obj):
        return obj.user.is_active
    is_active_user.boolean = True
    is_active_user.short_description = 'Активний'






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
    list_display = ['patient', 'phone', 'created_at', 'status']
    list_filter = ['status', 'created_at']
    search_fields = ['patient__username', 'phone', 'question']
    readonly_fields = ['created_at', 'answered_at']


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ['doctor', 'date', 'start_time', 'end_time', 'slot_duration']
    list_filter = ['doctor', 'date']
    search_fields = ['doctor__username']

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ['id', 'patient', 'doctor', 'date', 'status', 
        'status_label_display',   
        'cancelled_by',           
        'created_at']
    list_filter = ['status', 'date', 'cancelled_by']
    search_fields = ['patient__username', 'doctor__username']
    raw_id_fields = ['patient', 'doctor', 'cancelled_by']
    readonly_fields = ['created_at']

    def status_label_display(self, obj):
        """Відображення статусу з урахуванням, хто скасував"""
        return obj.status_label
    status_label_display.short_description = 'Статус (детально)'


@admin.register(QuestionMessage)
class QuestionMessageAdmin(admin.ModelAdmin):
    list_display = ['question', 'author', 'created_at']
    list_filter = ['created_at']
    search_fields = ['text', 'author__username']
    readonly_fields = ['created_at']




@admin.register(MedicalConclusion)
class MedicalConclusionAdmin(admin.ModelAdmin):
    list_display = ['patient', 'doctor', 'created_at']
    list_filter = ['created_at', 'doctor']
    search_fields = ['patient__username', 'doctor__username', 'diagnosis']
    readonly_fields = ['created_at']

# ===== ОБМЕЖЕННЯ ДОСТУПУ ДЛЯ ADMIN =====

def is_superuser_or_doctor(request):
    """Superuser або лікар — бачать медичні моделі"""
    if request.user.is_superuser:
        return True
    if hasattr(request.user, 'userprofile'):
        return request.user.userprofile.role == 'doctor'
    return False


# Приховати медичні моделі від звичайних admin
for model_admin in [
    HealthRecordAdmin, 
    AppointmentAdmin, 
    ScheduleAdmin,
    MedicalConclusionAdmin, 
    QuestionAdmin, 
    QuestionMessageAdmin
]:
    model_admin.has_module_permission = lambda self, request: is_superuser_or_doctor(request)
    model_admin.has_view_permission = lambda self, request, obj=None: is_superuser_or_doctor(request)
    model_admin.has_change_permission = lambda self, request, obj=None: is_superuser_or_doctor(request)
    model_admin.has_add_permission = lambda self, request: is_superuser_or_doctor(request)
    model_admin.has_delete_permission = lambda self, request, obj=None: is_superuser_or_doctor(request)