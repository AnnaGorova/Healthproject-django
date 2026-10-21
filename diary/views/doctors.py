from django.shortcuts import render
from ..models import UserProfile, HealthRecord, Question
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from ..models import Appointment
from datetime import date
from django.utils import timezone
from django.db import models
from ..models import MedicalConclusion
from .access import doctor_can_access_patient, get_accessible_patients
from .records import records


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
    patients_count = get_accessible_patients(user_profile).count()

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
