from django.shortcuts import render, redirect
from .models import UserProfile, HealthRecord, Question
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView
from .forms.doctor_question import DoctorQuestionForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from .forms import HealthRecordForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from .forms.user_profile import UserProfileForm
from .forms.appointment import AppointmentForm
from .models import Appointment, Schedule
from datetime import date, datetime, timedelta, time
from django.utils import timezone
from django.db import models
from .models import QuestionMessage
from .models import MedicalConclusion
from .forms.doctor_profile import DoctorProfileForm
from .models import DoctorProfile
from .models import ICD10Code
from dal import autocomplete
from django.http import JsonResponse
from django.db.models import Q, Count
from .forms.conclusion import MedicalConclusionForm
from django.http import Http404
from datetime import datetime as dt_class
import re


def is_admin_or_superuser(user):
    """Перевірка: адмін або супер_адмін"""
    if user.is_superuser:
        return True
    if hasattr(user, 'userprofile') and user.userprofile.role == 'admin':
        return True
    return False


def get_accessible_patients(doctor_profile):
    """
    Пацієнти, доступні лікарю:
    1. Закріплені (patient.doctor == лікар)
    2. Прийоми, які НЕ скасовані (scheduled АБО completed)
    
    Скасований прийом (cancelled) — НЕ дає доступу.
    """
    return UserProfile.objects.filter(
        role='patient'
    ).filter(
        Q(doctor=doctor_profile) |
        Q(appointments__doctor=doctor_profile,
          appointments__status__in=['scheduled', 'completed'])
    ).distinct()


def doctor_can_access_patient(doctor_profile, patient_profile):
    """Перевірка доступу лікаря до конкретного пацієнта"""
    if not patient_profile or patient_profile.role != 'patient':
        return False
    
    if patient_profile.doctor == doctor_profile:
        return True
    
    return Appointment.objects.filter(
        doctor=doctor_profile,
        patient=patient_profile,
        status__in=['scheduled', 'completed']
    ).exists()




def get_available_slots(doctor, days=14):
    """
    Повертає список доступних слотів для лікаря.
    
    Структура:
    [
        {
            'date': date(2026, 10, 14),
            'date_str': '2026-10-14',
            'day_name': 'Середа',
            'slots': [
                {'time': '09:00', 'datetime': datetime(2026, 10, 14, 9, 0), 'is_booked': False},
                ...
            ]
        },
        ...
    ]
    
    Використовується і для показу, і для валідації POST.
    """
   
    
    DAYS_UA = {
        0: 'Понеділок', 1: 'Вівторок', 2: 'Середа', 3: 'Четвер',
        4: 'П\'ятниця', 5: 'Субота', 6: 'Неділя',
    }
    
    slots_by_day = []
    today = date.today()
    now = timezone.now()
    
    for i in range(days):
        current_date = today + timedelta(days=i)
        day_of_week = current_date.weekday()
        
        # Розклад на цю дату
        day_schedules = Schedule.objects.filter(doctor=doctor, date=current_date)
        
        if day_schedules.exists():
            if day_schedules.filter(is_day_off=True).exists():
                continue
            schedules_to_use = day_schedules.exclude(is_day_off=True)
        else:
            if day_of_week > 4:
                continue
            schedules_to_use = [{
                'start_time': time(8, 0),
                'end_time': time(17, 0),
                'slot_duration': 30,
            }]
           
        day_slots = []
        for schedule in schedules_to_use:
            if isinstance(schedule, dict):
                start = schedule['start_time']
                end = schedule['end_time']
               
            else:
                start = schedule.start_time
                end = schedule.end_time
            duration = 30
            
            current_time = dt_class.combine(current_date, start)
            end_datetime = dt_class.combine(current_date, end)
            
            while current_time + timedelta(minutes=duration) <= end_datetime:
                # Тільки майбутні
                if timezone.make_aware(current_time) > now:
                    is_booked = Appointment.objects.filter(
                        doctor=doctor,
                        date=current_time,
                        status='scheduled'
                    ).exists()
                    
                    day_slots.append({
                        'time': current_time.strftime('%H:%M'),
                        'datetime': current_time,
                        'is_booked': is_booked,
                    })
                
                current_time += timedelta(minutes=duration)
        
        if day_slots:
            slots_by_day.append({
                'date': current_date,
                'date_str': current_date.strftime('%Y-%m-%d'),
                'day_name': DAYS_UA[current_date.weekday()],
                'slots': day_slots,
            })
    
    return slots_by_day


def is_slot_available(doctor, date_str, time_str):
    """
    Перевірка: чи є слот доступним для бронювання.
    
    Повертає:
    - (True, None) — слот доступний
    - (False, 'повідомлення') — слот недоступний з причиною
    
    ОПТИМІЗОВАНО: не викликає get_available_slots,
    перевіряє тільки конкретний слот (2-3 запити до БД).
    """
    
    # 1. Парсинг дати
    try:
        parsed_date = dt_class.strptime(date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return False, "❌ Некоректний формат дати"
    
    # 2. Парсинг часу
    try:
        parsed_time = dt_class.strptime(time_str, '%H:%M').time()
    except (ValueError, TypeError):
        return False, "❌ Некоректний формат часу"
    
    # 3. Комбінуємо
    appointment_datetime = dt_class.combine(parsed_date, parsed_time)
    
    # 4. Майбутнє?
    if timezone.make_aware(appointment_datetime) <= timezone.now():
        return False, "❌ Не можна бронювати минулий час"
    
    # 5. Знаходимо розклад лікаря на цю дату
    day_schedules = Schedule.objects.filter(doctor=doctor, date=parsed_date)
    
    if day_schedules.exists():
        # Є свій розклад
        if day_schedules.filter(is_day_off=True).exists():
            return False, "❌ Лікар не працює в цей день"
        
        schedules_to_check = day_schedules.exclude(is_day_off=True)
    else:
        # Немає розкладу — використовуємо дефолт (Пн-Пт, 8:00-17:00)
        if parsed_date.weekday() > 4:
            return False, "❌ Лікар не працює в цей день"
        
        schedules_to_check = [{
            'start_time': time(8, 0),
            'end_time': time(17, 0),
            'slot_duration': 30,
        }]
    
    # 6. Перевіряємо, що час відповідає сітці слотів
    is_valid_slot = False
    
    for schedule in schedules_to_check:
        if isinstance(schedule, dict):
            start = schedule['start_time']
            end = schedule['end_time']
            
        else:
            start = schedule.start_time
            end = schedule.end_time
        duration = 30
        
        # Генеруємо слоти для цього розкладу
        current_time = dt_class.combine(parsed_date, start)
        end_datetime = dt_class.combine(parsed_date, end)
        
        while current_time + timedelta(minutes=duration) <= end_datetime:
            if current_time == appointment_datetime:
                is_valid_slot = True
                break
            
            current_time += timedelta(minutes=duration)
        
        if is_valid_slot:
            break
    
    if not is_valid_slot:
        return False, "❌ Цей час недоступний (не відповідає сітці слотів)"
    
    # 7. Перевіряємо зайнятість
    is_booked = Appointment.objects.filter(
        doctor=doctor,
        date=appointment_datetime,
        status='scheduled'
    ).exists()
    
    if is_booked:
        return False, "❌ Цей час вже зайнятий"
    
    # 8. Все OK
    return True, None


def old_home(request):
    return redirect('/')


class HomeView(TemplateView):
    template_name = 'diary/home.html'

class AboutView(TemplateView):
    template_name = "diary/about.html" 


@login_required
def records(request):
    user_profile = request.user.userprofile

    # 1. Явна заборона 
    if is_admin_or_superuser(request.user):
        raise PermissionDenied("Адміністратори не мають доступу до медичних записів")

    # 2. Безпечний default (порожній queryset)
    all_records = HealthRecord.objects.none()

    # 3. Основна логіка
    if user_profile.role == 'patient':
        all_records = HealthRecord.objects.filter(user=user_profile, is_active=True)
    elif user_profile.role == 'doctor':
        accessible_patients = get_accessible_patients(user_profile)
        all_records = HealthRecord.objects.filter(
            user__in=accessible_patients,
            is_active=True
        )
    else:
        # 4. Аномалія (нова роль тощо) → 404
        raise Http404("Сторінку не знайдено")

    context = {
        'records': all_records,
        'user_profile': user_profile,
    }
    return render(request, 'diary/records.html', context)


@login_required
def user_records(request, user_id):
    # 1. Явна заборона для адмінів
    if is_admin_or_superuser(request.user):
        raise PermissionDenied("Адміністратори не мають доступу")

    target_user = get_object_or_404(UserProfile, id=user_id)
    current_user = request.user.userprofile

    # 2. Пацієнт — тільки себе
    if current_user.role == 'patient' and current_user.id != target_user.id:
        raise PermissionDenied("Ви не маєте доступу до записів іншого користувача")
    
    # 3. Лікар — тільки доступних пацієнтів
    if current_user.role == 'doctor':
        if not doctor_can_access_patient(current_user, target_user):
            raise PermissionDenied("Ви не маєте доступу до цього пацієнта")

    # 4. Аномалія
    if current_user.role not in ['patient', 'doctor']:
        raise Http404("Сторінку не знайдено")

    all_records = HealthRecord.objects.filter(user=target_user, is_active=True)

    context = {
        'records': all_records,
        'user_profile': target_user,
    }
    return render(request, 'diary/records.html', context)




@login_required
def record_detail(request, pk):
    # 1. Явна заборона для адмінів
    if is_admin_or_superuser(request.user):
        raise PermissionDenied("Адміністратори не мають доступу")

    user_profile = request.user.userprofile      
    
    # 2. Пацієнт — тільки свій запис
    if user_profile.role == 'patient':
        record = get_object_or_404(HealthRecord, id=pk, user=user_profile)
    # 3. Лікар — тільки записи доступних пацієнтів
    elif user_profile.role == 'doctor':
        accessible_patients = get_accessible_patients(user_profile)
        record = get_object_or_404(
            HealthRecord,
            id=pk,
            user__in=accessible_patients,
        )
    # 4. Аномалія
    else:
        raise Http404("Сторінку не знайдено")

    context = {
        'record': record,
        'record_date': record.date
    }
    return render(request, 'diary/record_detail.html', context)



   




def is_doctor(user):
    return user.is_authenticated and user.userprofile.role == 'doctor'

@login_required
def doctor_dashboard(request):
    """Дашборд лікаря"""
    user_profile = request.user.userprofile

    if user_profile.role != 'doctor':
        raise PermissionDenied("Тільки лікарі можуть бачити дашборд")

    now = timezone.now()
    today = timezone.localdate()

    # Прийоми на сьогодні (крім скасованих)
    today_appointments = Appointment.objects.filter(
        doctor=user_profile,
        date__date=today,
    ).exclude(
        status='cancelled'
    ).select_related('patient', 'conclusion').order_by('date')

    # Прийоми з попередніх днів без висновку
    past_pending_qs = Appointment.objects.filter(
        doctor=user_profile,
        status='scheduled',
        date__date__lt=today,
    )
    past_pending_count = past_pending_qs.count()
    past_pending = past_pending_qs.select_related('patient').order_by('date')[:10]

    # Останні висновки
    recent_conclusions = MedicalConclusion.objects.filter(
        doctor=user_profile
    ).select_related('patient', 'appointment').order_by('-created_at')[:5]

    # Нові звернення
    new_questions = Question.objects.filter(
        doctor=user_profile,
        status='new'
    ).order_by('-created_at')

    # Кількість пацієнтів
    patients_count = UserProfile.objects.filter(
        role='patient',
        appointments__doctor=user_profile
    ).distinct().count()

    return render(request, 'diary/doctor_dashboard.html', {
        'now': now,
        'today_appointments': today_appointments,
        'past_pending': past_pending,
        'past_pending_count': past_pending_count,
        'recent_conclusions': recent_conclusions,
        'new_questions': new_questions,
        'patients_count': patients_count,
    })



@login_required
def doctor_patients(request):
    """Список пацієнтів лікаря з пошуком"""
    user_profile = request.user.userprofile
    
    if user_profile.role != 'doctor':
        raise PermissionDenied("Тільки лікарі можуть бачити пацієнтів")
    
    patients = UserProfile.objects.filter(
        role='patient',
        appointments__doctor=user_profile
    ).distinct().order_by('username')
    
    search = request.GET.get('search', '').strip()
    if search:
        patients = patients.filter(
            models.Q(username__icontains=search) |
            models.Q(phone__icontains=search)
        )

    # Фільтр: стать
    gender = request.GET.get('gender', '').strip()
    if gender:
        patients = patients.filter(gender=gender)
    
    # Фільтр: вік
    age_from = request.GET.get('age_from', '').strip()
    age_to = request.GET.get('age_to', '').strip()
    
    today = date.today()
    
    if age_from:
        try:
            max_date = today.replace(year=today.year - int(age_from))
            patients = patients.filter(date_of_birth__lte=max_date)
        except ValueError:
            pass
    
    if age_to:
        try:
            min_date = today.replace(year=today.year - int(age_to) - 1)
            patients = patients.filter(date_of_birth__gte=min_date)
        except ValueError:
            pass
    
    return render(request, 'diary/doctor_patients.html', {
        'patients': patients,
        'search': search,
        'gender': gender,
        'age_from': age_from,
        'age_to': age_to,
    })
 


@login_required
def profile(request):
    
    user_profile = request.user.userprofile
   
    
    context = {
        'user_profile': user_profile,
    }
    return render(request, 'diary/profile.html', context)


@login_required
def edit_profile(request):
    user_profile = request.user.userprofile
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=user_profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Профіль оновлено!")
            return redirect('profile')
    else:
        form = UserProfileForm(instance=user_profile)
    
    return render(request, 'diary/edit_profile.html', {
        'user_profile': user_profile,
        'form': form,
    })


@login_required   
def users_list(request):
    current_user = request.user.userprofile

    if current_user.role == 'admin':
        patients = UserProfile.objects.filter(role='patient')
        doctors = UserProfile.objects.filter(role="doctor")
        admins = UserProfile.objects.filter(role ='admin')
    elif current_user.role == 'doctor':
        patients = current_user.patients.all()
        doctors = UserProfile.objects.filter(id=current_user.id) 
        admins = []
    else:
        patients = UserProfile.objects.filter(id=current_user.id)
        doctors = UserProfile.objects.filter(role='doctor')
        admins = []

    context = {
        'patients': patients,
        'doctors': doctors,
        'admins': admins,
        'users_count': UserProfile.objects.count(),
    }
    
    return render(request, 'diary/users_list.html', context)     


def is_admin(user):
  return user.is_authenticated and user.userprofile.role == 'admin'   

@user_passes_test(is_admin)
def administrator(request):
    return render(request, 'diary/administrator.html')

@login_required
def ask_question(request):
    user_profile = request.user.userprofile
       
    # Тільки пацієнти
    if user_profile.role != 'patient':
        raise PermissionDenied("Тільки пацієнти можуть задавати питання")

    if request.method == 'POST':
        form = DoctorQuestionForm(request.POST)
        if form.is_valid():
            question = form.save(commit=False)
            question.patient = request.user.userprofile 
            question.save()
            return render(request, 'diary/question_sent.html', {
                'data': form.cleaned_data,
                'user_profile': request.user.userprofile,
            })
    else:
        form = DoctorQuestionForm()
    return render(request, 'diary/ask_question.html', {'form': form})


@login_required  
def my_questions(request):
    # Заборона для адмінів
    if is_admin_or_superuser(request.user):
        raise PermissionDenied("Адміністратори не мають доступу")
    
    user_profile = request.user.userprofile
    # Тільки пацієнти
    if user_profile.role != 'patient':
        raise PermissionDenied("Тільки пацієнти можуть бачити свої питання")
    
    questions = Question.objects.filter(patient=user_profile).order_by('-created_at')
    return render(request, 'diary/my_questions.html', {'questions': questions})


@login_required
def all_questions(request):
    # 1. Явна заборона для адмінів
    if is_admin_or_superuser(request.user):
        raise PermissionDenied("Адміністратори не мають доступу до звернень")

    current_user = request.user.userprofile
    
    # 2. Тільки лікар
    if current_user.role != 'doctor':
        raise PermissionDenied("Доступ заборонено")
    
    # 3. Тільки свої звернення
    questions = Question.objects.filter(doctor=current_user).order_by('-created_at')
    
    return render(request, 'diary/all_questions.html', {
        'questions': questions,
    })



@login_required
def create_record(request):
    user_profile = request.user.userprofile
    # Заборона для адмінів
    if is_admin_or_superuser(request.user):
        raise PermissionDenied("Адміністратори не мають доступу")

    #  Тільки пацієнти можуть створювати записи
    if user_profile.role != 'patient':
        raise PermissionDenied("Тільки пацієнти можуть створювати записи")

    if request.method == 'POST':
        form = HealthRecordForm(request.POST)
        if form.is_valid():
            try:
                record = form.save(commit=False)
                record.user = request.user.userprofile
                record.save()
                
                messages.success(request, "Запис в щоденнику успішно створений!")
                return redirect('records')
            except Exception as e:
                    messages.error(request, f"Помилка при збереженні: {e}")
        else:
            messages.error(request, "Будь ласка, виправте помилки у формі.")
    else:
        form = HealthRecordForm()
    return render (request, 'diary/create_record.html', {'form': form})
        

@login_required
def my_records(request):
    # Заборона для адмінів
    if is_admin_or_superuser(request.user):
        raise PermissionDenied("Адміністратори не мають доступу")

    user_profile = request.user.userprofile

    #  Тільки пацієнти
    if user_profile.role != 'patient':
        raise PermissionDenied("Тільки пацієнти можуть бачити свої записи")
    
    
    records = HealthRecord.objects.filter(user=user_profile, is_active=True)
    return render(request, 'diary/my_records.html', {'records': records})



@login_required
def edit_record(request, pk):
    record = get_object_or_404(HealthRecord, id=pk)
    current_user = request.user.userprofile
    
    # Заборона для адмінів
    if is_admin_or_superuser(request.user):
        raise PermissionDenied("Адміністратори не мають доступу")

    if record.user != current_user:
        raise PermissionDenied("Ви не можете редагувати чужий запис")
    
    if request.method == 'POST':
        form = HealthRecordForm(request.POST, instance=record)
        if form.is_valid():
            form.save()
            messages.success(request, "Запис успішно оновлений!")
            return redirect('record_detail', pk=record.id)
    else:
        form = HealthRecordForm(instance=record)

    return render(request, 'diary/edit_record.html', {'form': form, 'record': record})




@login_required
def delete_record(request, pk):
    record = get_object_or_404(HealthRecord, id=pk)
   
    # Заборона для адмінів
    if is_admin_or_superuser(request.user):
        raise PermissionDenied("Адміністратори не мають доступу")

    if record.user != request.user.userprofile:
        raise PermissionDenied("Ви не можете видалити чужий запис")
    
    if request.method == 'POST':
        record.delete()
        messages.success(request, "Запис успішно видалено!")
        return redirect('my_records')
    
    return render(request, 'diary/delete_record.html', {'record': record})




def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        # ===== ДОДАТКОВА ПЕРЕВІРКА EMAIL =====
        try:
            validate_email(email)
        except ValidationError:
            messages.error(request, 'Невірний формат email')
            return render(request, 'diary/login.html')


        try:
            user_obj = User.objects.get(email=email)
            
            if not user_obj.is_active:
                messages.error(request, 'Обліковий запис деактивовано. Зверніться до адміністратора.')
                return render(request, 'diary/login.html')
            
            
            user = authenticate(request, username=user_obj.username, password=password)
            
            if user is not None:
                login(request, user)
                return redirect('home')
            else:
                messages.error(request, 'Невірний пароль')
        except User.DoesNotExist:
            messages.error(request, 'Користувача з таким email не знайдено')
    
    return render(request, 'diary/login.html')


def logout_view(request):
    logout(request)
    return redirect('home')

@login_required
def book_appointment(request, doctor_id):
    """Запис до конкретного лікаря"""
    doctor = get_object_or_404(UserProfile, id=doctor_id, role='doctor')
    user_profile = request.user.userprofile
    
    if user_profile.role != 'patient':
        raise PermissionDenied("Тільки пацієнти можуть записуватися")
    
    if request.method == 'POST':
        date_str = request.POST.get('date', '').strip()
        time_str = request.POST.get('time', '').strip()
        complaints = request.POST.get('complaints', '').strip()
        
        # 1. Перевірка наявності
        if not date_str or not time_str:
            messages.error(request, "⚠️ Оберіть дату та час")
            return redirect('book_appointment', doctor_id=doctor_id)
        
        # 2. Перевірка доступності слоту
        is_available, error_message = is_slot_available(doctor, date_str, time_str)
        
        if not is_available:
            messages.error(request, error_message)
            return redirect('book_appointment', doctor_id=doctor_id)
        
        # 3. Створюємо прийом
        appointment_datetime = dt_class.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        
        Appointment.objects.create(
            patient=user_profile,
            doctor=doctor,
            date=appointment_datetime,
            complaints=complaints,
        )
        messages.success(request, "✅ Ви успішно записані!")
        return redirect('my_appointments')
    
    # GET — показуємо доступні слоти
    slots = get_available_slots(doctor, days=14)
    
    return render(request, 'diary/book_appointment.html', {
        'doctor': doctor,
        'slots': slots,
    })

@login_required
def cancel_appointment(request, appointment_id):
    """Скасування прийому: GET — підтвердження, POST — скасування"""
    appointment = get_object_or_404(
        Appointment, 
        id=appointment_id, 
        patient=request.user.userprofile
    )
    
    # Перевірка: чи можна скасувати
    if not appointment.can_cancel:
        if appointment.status != 'scheduled':
            messages.error(request, "❌ Цей запис вже не активний")
        else:
            messages.error(request, "❌ Скасувати можна не пізніше ніж за 24 години до прийому")
        return redirect('my_appointments')
    
    # POST — скасовуємо
    if request.method == 'POST':
        appointment.status = 'cancelled'
        appointment.cancelled_by = request.user.userprofile
        appointment.save()
        messages.success(request, "✅ Запис скасовано")
        return redirect('my_appointments')
    
    # GET — показуємо сторінку підтвердження
    return render(request, 'diary/cancel_confirm.html', {
        'appointment': appointment,
    })



@login_required
def reschedule_appointment(request, appointment_id):
    """Перенесення = скасувати старий + перейти на запис до того ж лікаря"""
    old_appointment = get_object_or_404(
        Appointment, 
        id=appointment_id, 
        patient=request.user.userprofile
    )
    
    if not old_appointment.can_cancel:
        messages.error(request, "❌ Перенести можна не пізніше ніж за 24 години")
        return redirect('my_appointments')
    
    # Скасовуємо старий
    old_appointment.status = 'cancelled'
    old_appointment.cancelled_by = request.user.userprofile
    old_appointment.save()
    
    messages.info(request, "🔄 Оберіть новий час для запису")
    
    # Переходимо на сторінку запису до того ж лікаря
    return redirect('book_appointment', doctor_id=old_appointment.doctor.id)


def filter_appointments(request, queryset):
    """Фільтрація й сортування прийомів за статусом через ?status=..."""
    status_map = {
        'active': 'scheduled',
        'completed': 'completed',
        'cancelled': 'cancelled',
    }

    current = request.GET.get('status', 'active')
    if current not in status_map and current != 'all':
        current = 'active'

    counts = queryset.aggregate(
        total=Count('id'),
        scheduled=Count('id', filter=Q(status='scheduled')),
        completed=Count('id', filter=Q(status='completed')),
        cancelled=Count('id', filter=Q(status='cancelled')),
    )

    if current in status_map:
        queryset = queryset.filter(status=status_map[current])

    # активні: найближчі першими; решта: найновіші першими
    queryset = queryset.order_by('date' if current == 'active' else '-date')

    return queryset, current, counts


@login_required
def my_appointments(request):
    # Заборона для адмінів
    if is_admin_or_superuser(request.user):
        raise PermissionDenied("Адміністратори не мають доступу")

    user_profile = request.user.userprofile
    #  Тільки пацієнти
    if user_profile.role != 'patient':
        raise PermissionDenied("Тільки пацієнти можуть бачити свої прийоми")
    
    appointments = Appointment.objects.filter(
        patient=user_profile
    ).select_related('doctor', 'cancelled_by')

    appointments, current_status, counts = filter_appointments(request, appointments)

    return render(request, 'diary/my_appointments.html', {
        'appointments': appointments,
        'current_status': current_status,
        'counts': counts,
    })



@login_required
def doctors_list(request):
    """Список всіх лікарів"""
    doctors = UserProfile.objects.filter(role='doctor')
    
    return render(request, 'diary/doctors_list.html', {
        'doctors': doctors,
    })



@login_required
def manage_schedule(request):
    """Налаштування розкладу лікаря"""
    user_profile = request.user.userprofile
    
    if user_profile.role != 'doctor':
        raise PermissionDenied("Тільки лікарі можуть налаштовувати розклад")
    
    schedules = Schedule.objects.filter(doctor=user_profile).order_by('date', 'start_time')
    today = date.today()
    
    if request.method == 'POST':
        date_str = request.POST.get('date')
        is_day_off = request.POST.get('is_day_off') == 'on'
        start = request.POST.get('start_time')
        end = request.POST.get('end_time')
        duration = 30

        # ===== ВАЛІДАЦІЯ =====
        if not date_str:
            messages.error(request, "⚠️ Оберіть дату")
        elif date_str < str(today):
            messages.error(request, "⚠️ Не можна додавати розклад на минулі дати")
          # чи вже є запис на цю дату
        elif Schedule.objects.filter(doctor=user_profile, date=date_str).exists():
            messages.error(request, "⚠️ На цю дату вже є запис. Спочатку видаліть його.")
        elif is_day_off:
            # ===== ПЕРЕВІРКА: чи є активні записи на цю дату =====
            existing_appointments = Appointment.objects.filter(
                doctor=user_profile,
                date__date=date_str,
                status='scheduled'
            )

            if existing_appointments.exists():
                count = existing_appointments.count()
                word = "запис" if count == 1 else "записи"
                messages.error(
                    request,
                    f"⚠️ На цю дату вже є {count} активний(і) {word}. "
                    f"Спочатку скасуйте або перенесіть їх, а потім додайте вихідний."
                )
            else:
                # ===== ВИХІДНИЙ =====
                Schedule.objects.create(
                    doctor=user_profile,
                    date=date_str,
                    is_day_off=True,
                    start_time=None,
                    end_time=None,
                    slot_duration=0,
                )
                messages.success(request, "✅ Вихідний додано")
                return redirect('manage_schedule')
        elif not start or not end:
            messages.error(request, "⚠️ Заповніть час початку і кінця")
        elif start >= end:
            messages.error(request, "⚠️ Час початку має бути раніше часу кінця")
        else:
            # ===== ЗВИЧАЙНИЙ РОЗКЛАД =====
            existing = Schedule.objects.filter(
                doctor=user_profile,
                date=date_str,
                is_day_off=False,
            ).filter(
                models.Q(start_time__lt=end) & models.Q(end_time__gt=start)
            )
            
            if existing.exists():
                messages.error(request, "⚠️ Цей час перетинається з існуючим розкладом")
            else:
                Schedule.objects.create(
                    doctor=user_profile,
                    date=date_str,
                    is_day_off=False,
                    start_time=start,
                    end_time=end,
                    slot_duration=30,
                )
                messages.success(request, "✅ Розклад додано")
                return redirect('manage_schedule')
    
    # Години для select (24-годинний формат)
    hours = [f"{h:02d}:{m:02d}" for h in range(7, 22) for m in [0, 30]]
    
    return render(request, 'diary/manage_schedule.html', {
        'schedules': schedules,
        'hours': hours,
        'today': today,
    })





@login_required
def delete_schedule(request, schedule_id):
    """Видалення запису розкладу"""
    schedule = get_object_or_404(
        Schedule, 
        id=schedule_id, 
        doctor=request.user.userprofile
    )
    schedule.delete()
    messages.success(request, "✅ Розклад видалено")
    return redirect('manage_schedule')


@login_required
def doctor_appointments(request):
    """Записи до лікаря (для лікаря)"""
    user_profile = request.user.userprofile

    if user_profile.role != 'doctor':
        raise PermissionDenied("Тільки лікарі можуть бачити цю сторінку")

    appointments = Appointment.objects.filter(
        doctor=user_profile
    ).select_related('patient', 'cancelled_by')

    appointments, current_status, counts = filter_appointments(request, appointments)

    return render(request, 'diary/doctor_appointments.html', {
        'appointments': appointments,
        'current_status': current_status,
        'counts': counts,
    })


@login_required
def answer_question(request, question_id):
    """Відповідь лікаря"""
    
    user_profile = request.user.userprofile
    
    if user_profile.role != 'doctor':
        raise PermissionDenied("Тільки лікарі можуть відповідати")

    # 1. Знаходимо питання за ID
    question = get_object_or_404(Question, id=question_id)
    
    # 2. Перевіряємо доступ → 403 (замість 404)
    if question.doctor != user_profile:
        raise PermissionDenied("Це питання адресовано іншому лікарю")
    
    if request.method == 'POST':
        answer = request.POST.get('answer', '').strip()
        close = request.POST.get('close') == 'on'
        
        if not answer:
            messages.error(request, "⚠️ Введіть відповідь")
        else:
            # Створюємо повідомлення
            QuestionMessage.objects.create(
                question=question,
                author=user_profile,
                text=answer,
            )
            
            question.doctor = user_profile
            question.answered_at = timezone.now()
            question.status = 'closed' if close else 'answered'
            question.save()
            
            messages.success(request, "✅ Відповідь надіслано")
            return redirect('all_questions')
    
    return render(request, 'diary/answer_question.html', {
        'question': question,
    })


@login_required
def reply_question(request, question_id):
    """Пацієнт продовжує діалог"""
    user_profile = request.user.userprofile
    
    # Тільки пацієнти
    if user_profile.role != 'patient':
        raise PermissionDenied("Тільки пацієнти можуть відповідати в діалозі")
    

    question = get_object_or_404(
        Question, 
        id=question_id, 
        patient=request.user.userprofile
    )
    
    if question.status == 'closed':
        messages.error(request, "❌ Це питання закрито")
        return redirect('my_questions')
    
    if request.method == 'POST':
        text = request.POST.get('text', '').strip()
        
        if not text:
            messages.error(request, "⚠️ Введіть повідомлення")
        else:
            QuestionMessage.objects.create(
                question=question,
                author=request.user.userprofile,
                text=text,
            )
            question.status = 'new'  # знову нове
            question.save()
            
            messages.success(request, "✅ Повідомлення надіслано")
            return redirect('my_questions')
    
    return render(request, 'diary/reply_question.html', {
        'question': question,
    })




@login_required
def patient_card(request, patient_id):
    """Картка пацієнта (для лікаря)"""
    user_profile = request.user.userprofile
    
    if user_profile.role != 'doctor':
        raise PermissionDenied("Тільки лікарі можуть переглядати картки")
    
    patient = get_object_or_404(UserProfile, id=patient_id, role='patient')

    # Використовуємо спільну функцію
    if not doctor_can_access_patient(user_profile, patient):
        raise PermissionDenied("Ви не маєте доступу до цього пацієнта")
    
    # Дані пацієнта
    records = HealthRecord.objects.filter(user=patient, is_active=True).order_by('date')[:10]
    appointments = Appointment.objects.filter(
        doctor=user_profile,
        patient=patient
    ).order_by('date')
    conclusions = MedicalConclusion.objects.filter(patient=patient).order_by('created_at')
    
    return render(request, 'diary/patient_card.html', {
        'patient': patient,
        'records': records,
        'appointments': appointments,
        'conclusions': conclusions,
    })



@login_required
def create_conclusion(request, appointment_id):
    """Створення висновку після прийому"""
    user_profile = request.user.userprofile

    if user_profile.role != 'doctor':
        raise PermissionDenied("Тільки лікарі можуть створювати висновки")

    appointment = get_object_or_404(
        Appointment,
        id=appointment_id,
        doctor=user_profile
    )
    # Перевірка: чи прийом уже відбувся
    if appointment.date > timezone.now():
        messages.error(request, "⚠️ Не можна створити висновок до початку прийому")
        return redirect('patient_card', patient_id=appointment.patient.id)

    # Перевірка: чи вже є висновок
    if hasattr(appointment, 'conclusion'):
        messages.warning(request, "⚠️ Висновок вже створено")
        return redirect('patient_card', patient_id=appointment.patient.id)

    # Перевірка: чи прийом не скасовано
    if appointment.status == 'cancelled':
        messages.error(request, "❌ Не можна створити висновок для скасованого прийому")
        return redirect('patient_card', patient_id=appointment.patient.id)


    if request.method == 'POST':
        form = MedicalConclusionForm(request.POST)
        if form.is_valid():
            conclusion = form.save(commit=False)
            conclusion.appointment = appointment
            conclusion.doctor = user_profile
            conclusion.patient = appointment.patient
            conclusion.save()

            appointment.status = 'completed'
            appointment.save()

            messages.success(request, "✅ Висновок створено")
            return redirect('patient_card', patient_id=appointment.patient.id)
    else:
        form = MedicalConclusionForm()

    return render(request, 'diary/create_conclusion.html', {
        'appointment': appointment,
        'form': form,
    })




@login_required
def edit_doctor_profile(request):
    """Редагування профілю лікаря"""
    user_profile = request.user.userprofile
    
    if user_profile.role != 'doctor':
        raise PermissionDenied("Тільки лікарі можуть редагувати цей профіль")
    
    # Отримуємо або створюємо DoctorProfile
    doctor_profile, created = DoctorProfile.objects.get_or_create(
        user=user_profile,
        defaults={
            'specialty': 'Терапевт',
            'year_of_experience': 0,
            'phone': '',
        }
    )
    
    if request.method == 'POST':
        form = DoctorProfileForm(request.POST, instance=doctor_profile)
        if form.is_valid():
            form.save()
            messages.success(request, "✅ Профіль оновлено")
            return redirect('profile')
    else:
        form = DoctorProfileForm(instance=doctor_profile)
    
    return render(request, 'diary/edit_doctor_profile.html', {
        'form': form,
        'doctor_profile': doctor_profile,
    })





@login_required
def view_conclusion(request, appointment_id):
    """Перегляд висновку пацієнтом"""
    user_profile = request.user.userprofile
    
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    # Перевірка: пацієнт — власник, або лікар цього прийому
    if user_profile.role == 'patient':
        if appointment.patient != user_profile:
            raise PermissionDenied("Це не ваш прийом")
    elif user_profile.role == 'doctor':
        if appointment.doctor != user_profile:
            raise PermissionDenied("Це не ваш прийом")
    else:
        raise PermissionDenied("Доступ заборонено")
    
    # Перевірка: чи є висновок
    if not hasattr(appointment, 'conclusion'):
        messages.error(request, "❌ Висновок ще не створено")
        return redirect('my_appointments')
    
    return render(request, 'diary/view_conclusion.html', {
        'appointment': appointment,
        'conclusion': appointment.conclusion,
    })



@login_required
def my_conclusions(request):
    """Всі висновки пацієнта"""
    user_profile = request.user.userprofile
    
    if user_profile.role != 'patient':
        raise PermissionDenied("Тільки пацієнти можуть бачити цю сторінку")
    
    conclusions = MedicalConclusion.objects.filter(
        patient=user_profile
    ).select_related('doctor', 'appointment').order_by('created_at')
    
    return render(request, 'diary/my_conclusions.html', {
        'conclusions': conclusions,
    })


@login_required
def icd10_autocomplete(request):
    """Пошук кодів МКХ-10 за кодом або назвою (JSON)"""
    user_profile = getattr(request.user, 'userprofile', None)

    if not user_profile or user_profile.role != 'doctor':
        return JsonResponse({'results': [], 'pagination': {'more': False}})

    q = request.GET.get('q', '').strip()

    qs = ICD10Code.objects.all()
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(code__istartswith=q)).distinct()

    qs = qs.order_by('code')[:50]

    results = [
        {'id': item.id, 'text': f"{item.code} — {item.name}"}
        for item in qs
    ]

    return JsonResponse({
        'results': results,
        'pagination': {'more': False},
    })





@login_required
def appointment_detail(request, appointment_id):
    """Деталі прийому для лікаря"""
    user_profile = request.user.userprofile

    if user_profile.role != 'doctor':
        raise PermissionDenied("Тільки лікарі можуть переглядати деталі прийому")

    appointment = get_object_or_404(
        Appointment,
        id=appointment_id,
        doctor=user_profile
    )

    return render(request, 'diary/appointment_detail.html', {
        'appointment': appointment,
    })


@login_required
def doctor_cancel_appointment(request, appointment_id):
    """Скасування прийому лікарем"""
    user_profile = request.user.userprofile

    if user_profile.role != 'doctor':
        raise PermissionDenied("Тільки лікарі можуть скасовувати прийоми")

    appointment = get_object_or_404(
        Appointment,
        id=appointment_id,
        doctor=user_profile
    )

    if appointment.status != 'scheduled':
        messages.error(request, "❌ Цей прийом вже не активний")
        return redirect('appointment_detail', appointment_id=appointment.id)

    if request.method == 'POST':
        appointment.status = 'cancelled'
        appointment.cancelled_by = user_profile
        appointment.save()
        messages.success(request, "✅ Прийом скасовано")
        return redirect('doctor_appointments')

    return render(request, 'diary/doctor_cancel_confirm.html', {
        'appointment': appointment,
    })





@login_required
def edit_conclusion(request, conclusion_id):
    """Редагування вже створеного висновку"""
    user_profile = request.user.userprofile

    if user_profile.role != 'doctor':
        raise PermissionDenied("Тільки лікарі можуть редагувати висновки")

    conclusion = get_object_or_404(
        MedicalConclusion,
        id=conclusion_id,
        doctor=user_profile
    )

    if request.method == 'POST':
        form = MedicalConclusionForm(request.POST, instance=conclusion)
        if form.is_valid():
            form.save()
            messages.success(request, "✅ Висновок оновлено")
            return redirect('view_conclusion', appointment_id=conclusion.appointment.id)
    else:
        form = MedicalConclusionForm(instance=conclusion)

    return render(request, 'diary/edit_conclusion.html', {
        'form': form,
        'conclusion': conclusion,
    })






# ===== МОДУЛЬ АДМІНІСТРАТОРА =====

@login_required
def administrator(request):
    """Кастомна сторінка адміністратора"""
    user_profile = request.user.userprofile
    
    if user_profile.role != 'admin':
        raise PermissionDenied("Тільки адміністратори мають доступ")
    
    users = User.objects.select_related('userprofile').order_by('-id')
    
    # Пошук
    search = request.GET.get('search', '').strip()
    if search:
        users = users.filter(
            models.Q(username__icontains=search) |
            models.Q(email__icontains=search) |
            models.Q(userprofile__username__icontains=search)
        )
    
    # Фільтр за роллю
    role = request.GET.get('role', '').strip()
    if role:
        users = users.filter(userprofile__role=role)
    
    return render(request, 'diary/administrator.html', {
        'users': users,
        'search': search,
        'role': role,
    })


@login_required
def admin_user_create(request):
    """Створення користувача адміном"""
    user_profile = request.user.userprofile
    
    if user_profile.role != 'admin':
        raise PermissionDenied("Тільки адміністратори мають доступ")
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        middle_name = request.POST.get('middle_name', '').strip()
        role = request.POST.get('role', 'patient')
        phone = request.POST.get('phone', '').strip()
        gender = request.POST.get('gender', '').strip()          
        date_of_birth = request.POST.get('date_of_birth', '').strip()  
        
        # Валідація
        if not username or not email:
            messages.error(request, "⚠️ Логін і email обов'язкові")
        elif User.objects.filter(username=username).exists():
            messages.error(request, "⚠️ Такий логін вже існує")
        elif User.objects.filter(email=email).exists():
            messages.error(request, "⚠️ Такий email вже існує")
        elif phone and not re.match(r'^\+?[\d\s\-\(\)]{10,20}$', phone): 
            messages.error(request, "⚠️ Некоректний телефон. Приклад: +380501234567")
        else:
            # Створення User (без пароля → сигнал надішле лист)
            user = User.objects.create_user(
                username=username,
                email=email,
                password=None,
            )
            user.first_name = first_name
            user.last_name = last_name
            user.save()
            
            # UserProfile створюється сигналом, але роль і телефон треба оновити
            profile = user.userprofile
            profile.role = role
            profile.phone = phone
            profile.middle_name = middle_name
            profile.username = f"{last_name} {first_name} {middle_name}".strip() or username
            
            
            if gender:
                profile.gender = gender
            if date_of_birth:
                profile.date_of_birth = date_of_birth
            
            profile.save()
            
            # Якщо лікар — створити DoctorProfile
            if role == 'doctor':
                DoctorProfile.objects.get_or_create(
                    user=profile,
                    defaults={
                        'specialty': 'Терапевт',
                        'year_of_experience': 0,
                        'phone': '',
                    }
                )
            
            messages.success(request, f"✅ Користувача {username} створено, лист надіслано")
            return redirect('administrator')
    
    return render(request, 'diary/admin_user_form.html', {
        'action': 'create',
    })



@login_required
def admin_user_edit(request, user_id):
    """Редагування користувача адміном"""
    user_profile = request.user.userprofile
    
    if user_profile.role != 'admin':
        raise PermissionDenied("Тільки адміністратори мають доступ")
    
    user = get_object_or_404(User, id=user_id)
    profile = user.userprofile
    
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        middle_name = request.POST.get('middle_name', '').strip()
        role = request.POST.get('role', 'patient')
        phone = request.POST.get('phone', '').strip()
        gender = request.POST.get('gender', '').strip()
        date_of_birth = request.POST.get('date_of_birth', '').strip()

        # ===== ВАЛІДАЦІЯ ТЕЛЕФОНУ =====
        if phone and not re.match(r'^\+?[\d\s\-\(\)]{10,20}$', phone):
            messages.error(request, "⚠️ Некоректний телефон. Приклад: +380501234567")
            return render(request, 'diary/admin_user_form.html', {    # ← ОСЬ ЦЕ ДОДАТИ!
                'action': 'edit',
                'user_obj': user,
                'profile': profile,
            })
        
        # Перевірка email (крім свого)
        if User.objects.filter(email=email).exclude(id=user.id).exists():
            messages.error(request, "⚠️ Такий email вже існує")
        else:
            user.email = email
            user.first_name = first_name
            user.last_name = last_name
            user.save()
            
            profile.role = role
            profile.phone = phone
            profile.middle_name = middle_name 
            profile.username = f"{last_name} {first_name} {middle_name}".strip() or user.username
            
            if gender:
                profile.gender = gender
            if date_of_birth:
                profile.date_of_birth = date_of_birth
            
            profile.save()
            
            if role == 'doctor':
                DoctorProfile.objects.get_or_create(
                    user=profile,
                    defaults={
                        'specialty': 'Терапевт',
                        'year_of_experience': 0,
                        'phone': '',
                    }
                )
            
            messages.success(request, "✅ Користувача оновлено")
            return redirect('administrator')
    
    return render(request, 'diary/admin_user_form.html', {
        'action': 'edit',
        'user_obj': user,
        'profile': profile,
    })


@login_required
def admin_user_toggle(request, user_id):
    """Деактивація / активація користувача"""
    user_profile = request.user.userprofile
    
    if user_profile.role != 'admin':
        raise PermissionDenied("Тільки адміністратори мають доступ")

    #  ТІЛЬКИ POST!
    if request.method != 'POST':
        messages.error(request, "❌ Некоректний метод запиту")
        return redirect('administrator')
    
    user = get_object_or_404(User, id=user_id)
    
    # Не можна деактивувати себе
    if user.id == request.user.id:
        messages.error(request, "❌ Не можна деактивувати себе")
        return redirect('administrator')
    
    # Не можна деактивувати superuser
    if user.is_superuser:
        messages.error(request, "❌ Не можна деактивувати суперкористувача")
        return redirect('administrator')
    
    user.is_active = not user.is_active
    user.save()
    
    status = "активовано" if user.is_active else "деактивовано"
    messages.success(request, f"✅ Користувача {user.username} {status}")
    return redirect('administrator')



def custom_404(request, exception):
    """404 Not Found"""
    return render(request, '404.html', status=404)