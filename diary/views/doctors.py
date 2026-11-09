from django.shortcuts import render, redirect
from django import forms
from ..models import UserProfile, HealthRecord, Question
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.paginator import Paginator
from ..models import Appointment
from datetime import date, datetime, time, timedelta
from django.utils import timezone
from django.db import models
from ..models import MedicalConclusion
from .access import doctor_can_access_patient, get_accessible_patients
from .records import records


@login_required
def doctor_dashboard(request):
    """Вибір доступного лікарю пацієнта для перегляду аналітики."""
    user_profile = request.user.userprofile

    if user_profile.role != 'doctor':
        raise PermissionDenied("Тільки лікарі можуть бачити дашборд")

    patients = get_accessible_patients(user_profile).order_by('username', 'pk')
    patient_field = forms.ModelChoiceField(
        queryset=patients,
        error_messages={
            'required': 'Оберіть пацієнта.',
            'invalid_choice': 'Оберіть пацієнта зі списку доступних.',
        },
    )
    selection_error = ''
    if 'patient' in request.GET:
        try:
            patient = patient_field.clean(request.GET.get('patient'))
        except ValidationError as error:
            selection_error = error.messages[0]
        else:
            return redirect('patient_analytics', patient_id=patient.pk)

    search = request.GET.get('search', '').strip()
    if search:
        patients = patients.filter(
            models.Q(username__icontains=search) |
            models.Q(phone__icontains=search)
        )
    patients_page = Paginator(patients, 20).get_page(request.GET.get('page'))

    context = get_doctor_home_context(user_profile)
    context.update({
        'patients': patients_page.object_list,
        'patients_page': patients_page,
        'search': search,
        'selection_error': selection_error,
    })
    return render(request, 'diary/doctor_dashboard.html', context)


def get_doctor_home_context(user_profile):
    """Спільні дані карток головної сторінки та детальних блоків дашборда."""
    now = timezone.now()
    today = timezone.localdate()
    notifications_from = timezone.make_aware(
        datetime.combine(today - timedelta(days=6), time.min)
    )
    accessible_patients = get_accessible_patients(user_profile)
    new_records = HealthRecord.objects.filter(
        user__in=accessible_patients,
        is_active=True,
        date__gte=notifications_from,
        date__lte=now,
    ).select_related('user').order_by('-date', '-pk')
    new_patients = accessible_patients.filter(
        user__date_joined__gte=notifications_from,
        user__date_joined__lte=now,
    ).order_by('-user__date_joined', '-pk')
    new_appointments = Appointment.objects.filter(
        doctor=user_profile,
        created_at__gte=notifications_from,
        created_at__lte=now,
    ).exclude(status='cancelled').select_related('patient').order_by('-created_at', '-pk')

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
    ).select_related('patient', 'appointment', 'icd10').order_by('-created_at')[:5]

    # Нові звернення
    new_questions = Question.objects.filter(
        doctor=user_profile,
        status='new'
    ).select_related('patient').order_by('-created_at')

    return {
        'now': now,
        'today_appointments': today_appointments,
        'past_pending': past_pending,
        'past_pending_count': past_pending_count,
        'recent_conclusions': recent_conclusions,
        'new_questions': new_questions,
        'new_records_count': new_records.count(),
        'new_records': new_records[:10],
        'new_patients_count': new_patients.count(),
        'new_patients': new_patients[:10],
        'new_appointments_count': new_appointments.count(),
        'new_appointments': new_appointments[:10],
    }


@login_required
def doctor_patients(request):
    """Список пацієнтів лікаря з пошуком"""
    user_profile = request.user.userprofile
    
    if user_profile.role != 'doctor':
        raise PermissionDenied("Тільки лікарі можуть бачити пацієнтів")
    
    patients = (
        get_accessible_patients(user_profile)
        .select_related('user')
        .order_by('username')
    )
    
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
            patients = patients.filter(date_of_birth__gt=min_date)
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
def users_list(request):
    current_user = request.user.userprofile

    if current_user.role == 'admin':
        patients = UserProfile.objects.filter(role='patient')
        doctors = UserProfile.objects.filter(role="doctor")
        admins = UserProfile.objects.filter(role ='admin')
    elif current_user.role == 'doctor':
        patients = (
            get_accessible_patients(current_user)
            .select_related('user')
            .order_by('username')
        )
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


@login_required
def doctors_list(request):
    """Список всіх лікарів"""
    doctors = UserProfile.objects.filter(
        role='doctor',
        user__is_active=True,
    )
    
    return render(request, 'diary/doctors_list.html', {
        'doctors': doctors,
    })


@login_required
def patient_card(request, patient_id):
    """Картка пацієнта (для лікаря)"""
    user_profile = request.user.userprofile
    
    if user_profile.role != 'doctor':
        raise PermissionDenied("Тільки лікарі можуть переглядати картки")
    
    patient = get_object_or_404(UserProfile.objects.select_related('user'), id=patient_id, role='patient')

    # Використовуємо спільну функцію
    if not doctor_can_access_patient(user_profile, patient):
        raise PermissionDenied("Ви не маєте доступу до цього пацієнта")
    
    # Дані пацієнта
    active_records = HealthRecord.objects.filter(user=patient, is_active=True).order_by('-date', '-pk')
    records = active_records[:10]
    parameters = []
    for key, label, unit, theme, icon in [
        ('temperature', 'Температура', '°C', 'mint', 'temperature.svg'),
        ('heart_rate', 'Пульс', 'уд/хв', 'pink', 'pulse.svg'),
        ('pressure', 'Артеріальний тиск', 'мм рт. ст.', 'yellow', 'blood-pressure.svg'),
        ('spo2', 'SpO₂', '%', 'blue', 'spo2.svg'),
        ('blood_sugar', 'Глюкоза', 'ммоль/л', 'purple', 'glucose.svg'),
    ]:
        fields = ['pressure_systolic', 'pressure_diastolic'] if key == 'pressure' else [key]
        measurement = active_records.filter(**{f'{field}__isnull': False for field in fields}).first()
        value = None
        if measurement is not None:
            value = '/'.join(f'{getattr(measurement, field):g}' for field in fields)
        parameters.append({
            'label': label, 'value': value, 'unit': unit, 'theme': theme,
            'icon': 'diary/images/' + icon,
            'date': measurement.date if measurement else None,
        })
    appointments = Appointment.objects.filter(
        doctor=user_profile,
        patient=patient
    ).select_related('doctor', 'cancelled_by', 'conclusion').order_by('-date', '-pk')
    
    return render(request, 'diary/patient_card.html', {
        'patient': patient,
        'records': records,
        'appointments': appointments,
        'patient_parameters': parameters,
    })
