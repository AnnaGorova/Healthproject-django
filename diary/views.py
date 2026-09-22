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

def old_home(request):
    return redirect('/')


class HomeView(TemplateView):
    template_name = 'diary/home.html'

class AboutView(TemplateView):
    template_name = "diary/about.html" 


@login_required
def records(request):
    user_profile = request.user.userprofile

    if user_profile.role == 'patient':
        all_records = HealthRecord.objects.filter(user=user_profile, is_active=True)
    elif user_profile.role == 'doctor':
        patient_ids = user_profile.patients.values_list('id', flat=True)
        all_records = HealthRecord.objects.filter(user_id__in=patient_ids, is_active=True)
    else:
        all_records = HealthRecord.objects.all()
    
    
       
    context = {
        'records': all_records,
        'user_profile': user_profile,
       
    }
    
    return render(request, 'diary/records.html', context)


@login_required
def user_records(request, user_id):
    target_user = get_object_or_404(UserProfile, id=user_id)
    current_user = request.user.userprofile

    if current_user.role == 'patient' and current_user.id != target_user.id:
        raise PermissionDenied("Ви не маєте доступу до записів іншого користувача")
    
    if current_user.role == 'doctor' and target_user.role == 'patient':
        if target_user.doctor != current_user:
            raise PermissionDenied("Отримайте доступ")

    all_records = HealthRecord.objects.filter(user=target_user, is_active=True)

    context = {
        'records': all_records,
        'user_profile': target_user,
    }

    return render(request, 'diary/records.html', context)

@login_required
def record_detail(request, pk):
    record = get_object_or_404(HealthRecord, id=pk)
    user_profile = request.user.userprofile      
    
    if user_profile.role == 'patient':
        record = get_object_or_404(HealthRecord, id=pk, user=user_profile)
    else: 
        record = get_object_or_404(HealthRecord, id=pk)

    context = {
        'record': record,
        'record_date': record.date
    }

    return render(request, 'diary/record_detail.html', context)

@login_required
def doctor_patients(request):
    current_user = request.user.userprofile

    if current_user.role not in ['doctor', 'admin']:
        raise PermissionDenied("Ця сторінка доступна тільки для лікаря або адміністратора")
    
    if current_user.role == 'doctor':
        patients = current_user.patients.all()
    else:  
        patients = UserProfile.objects.filter(role='patient')

        

    context = {
        'doctor' : current_user,
        'patients' : patients,
    }
    return render(request, 'diary/doctor_patients.html', context)



def is_doctor(user):
    return user.is_authenticated and user.userprofile.role == 'doctor'

@user_passes_test(is_doctor)
def doctor_dashboard(request):
    doctor = request.user.userprofile
    patients = doctor.patients.all()

    context = {
        'doctor': doctor,
        'patients': patients,
    }

    return render(request, 'diary/doctor_patients.html', context)







 


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
    user_profile = request.user.userprofile
    questions = Question.objects.filter(patient=user_profile).order_by('-created_at')
    return render(request, 'diary/my_questions.html', {'questions': questions})



@login_required
def all_questions(request):
    current_user = request.user.userprofile
    
    if current_user.role not in ['doctor', 'admin']:
        raise PermissionDenied("Доступ заборонено")
    
    if current_user.role == 'doctor':
        questions = Question.objects.filter(
            doctor=current_user
        ).order_by('-created_at')
    else:
        questions = Question.objects.all().order_by('-created_at')
    
    return render(request, 'diary/all_questions.html', {
        'questions': questions,
    })



@login_required
def create_record(request):
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
    user_profile = request.user.userprofile
    records = HealthRecord.objects.filter(user = user_profile, is_active=True)
    return render(request, 'diary/my_records.html', {'records': records})




@login_required
def edit_record(request, pk):
    record = get_object_or_404(HealthRecord, id=pk)
    current_user = request.user.userprofile

   
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
        date_str = request.POST.get('date')
        time_str = request.POST.get('time')
        complaints = request.POST.get('complaints', '')

        if not date_str or not time_str:
            messages.error(request, "⚠️ Будь ласка, оберіть дату та час")
            return redirect('book_appointment', doctor_id=doctor_id)
        
        appointment_date = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        
        if Appointment.objects.filter(
            doctor=doctor, 
            date=appointment_date,
            status='scheduled'
        ).exists():
            messages.error(request, "Цей час вже зайнятий")
        else:
            Appointment.objects.create(
                patient=user_profile,
                doctor=doctor,
                date=appointment_date,
                complaints=complaints,
            )
            messages.success(request, "Ви успішно записані!")
            return redirect('my_appointments')
    
    # ===== ГЕНЕРАЦІЯ СЛОТІВ =====
    slots = []
    today = date.today()
    now = timezone.now()

    DAYS_UA = {
        0: 'Понеділок',
        1: 'Вівторок',
        2: 'Середа',
        3: 'Четвер',
        4: 'П\'ятниця',
        5: 'Субота',
        6: 'Неділя',
    }

    # ===== ГІБРИДНА ЛОГІКА: свій розклад + дефолт =====
    for i in range(14):
        current_date = today + timedelta(days=i)
        day_of_week = current_date.weekday()
        
        # Шукаємо розклад на цю дату
        day_schedules = Schedule.objects.filter(
            doctor=doctor,
            date=current_date
        )
        
        if day_schedules.exists():
            # чи це вихідний?
            if day_schedules.filter(is_day_off=True).exists():
                continue  # Пропустити день
            
            # Є свій розклад → використовуємо (без вихідних)
            schedules_to_use = day_schedules.exclude(is_day_off=True)
        else:
            # Немає → використовуємо дефолт (тільки Пн-Пт)
            if day_of_week > 4:
                continue  # Сб, Нд — вихідний
            
            # Дефолт: 8:00-17:00, 30 хв
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
                duration = schedule['slot_duration']
            else:
                start = schedule.start_time
                end = schedule.end_time
                duration = schedule.slot_duration
            
            current_time = datetime.combine(current_date, start)
            end_datetime = datetime.combine(current_date, end)
            
            while current_time < end_datetime:
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
            slots.append({
                'date': current_date,
                'date_str': current_date.strftime('%Y-%m-%d'),
                'day_name': DAYS_UA[current_date.weekday()],
                'slots': day_slots,
            })
    
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
    old_appointment.save()
    
    messages.info(request, "🔄 Оберіть новий час для запису")
    
    # Переходимо на сторінку запису до того ж лікаря
    return redirect('book_appointment', doctor_id=old_appointment.doctor.id)

@login_required
def my_appointments(request):
    user_profile = request.user.userprofile
    appointments = Appointment.objects.filter(patient=user_profile).order_by('date')
    
    return render(request, 'diary/my_appointments.html', {
        'appointments': appointments,
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
        duration = request.POST.get('slot_duration', 30)
        
        # ===== ВАЛІДАЦІЯ =====
        if not date_str:
            messages.error(request, "⚠️ Оберіть дату")
        elif date_str < str(today):
            messages.error(request, "⚠️ Не можна додавати розклад на минулі дати")
          # чи вже є запис на цю дату
        elif Schedule.objects.filter(doctor=user_profile, date=date_str).exists():
            messages.error(request, "⚠️ На цю дату вже є запис. Спочатку видаліть його.")

        elif is_day_off:
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
                    slot_duration=int(duration),
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
    ).order_by('date')
    
    return render(request, 'diary/doctor_appointments.html', {
        'appointments': appointments,
    })



@login_required
def answer_question(request, question_id):
    """Відповідь лікаря"""
    question = get_object_or_404(Question, id=question_id)
    user_profile = request.user.userprofile
    
    if user_profile.role != 'doctor':
        raise PermissionDenied("Тільки лікарі можуть відповідати")

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