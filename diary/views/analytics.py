from django.shortcuts import render
from ..models import UserProfile, HealthRecord
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from datetime import timedelta
from django.utils import timezone
from django.db.models import Avg, Min, Max
from .access import doctor_can_access_patient
from .records import records


@login_required
def health_analytics(request, patient_id=None):
    """
    Аналітика здоров'я.
    - Пацієнт → своя аналітика
    - Лікар → аналітика свого пацієнта
    """
        
    current_user = request.user.userprofile
    
    # ===== ВИЗНАЧАЄМО, ЧИЮ АНАЛІТИКУ ПОКАЗУЄМО =====
    if patient_id:
        # Лікар дивиться пацієнта
        if current_user.role != 'doctor':
            raise PermissionDenied("Тільки лікарі можуть переглядати аналітику пацієнтів")
        
        patient = get_object_or_404(UserProfile, id=patient_id, role='patient')
        
        if not doctor_can_access_patient(current_user, patient):
            raise PermissionDenied("Ви не маєте доступу до цього пацієнта")
    else:
        # Пацієнт дивиться себе
        if current_user.role != 'patient':
            raise PermissionDenied("Тільки пацієнти мають особисту аналітику")
        
        patient = current_user
    
    # ===== ПЕРІОД =====
    period = request.GET.get('period', 'month')
    period_days = {
        'week': 7,
        'month': 30,
        'year': 365,
    }
    days = period_days.get(period, 30)
    date_from = timezone.now() - timedelta(days=days)
    
    # ===== ЗАПИСИ ЗА ПЕРІОД =====
    records = HealthRecord.objects.filter(
        user=patient,
        is_active=True,
        date__gte=date_from,
    ).order_by('date')
    
    # ===== СТАТИСТИКА =====
    stats = records.aggregate(
        avg_temp=Avg('temperature'),
        min_temp=Min('temperature'),
        max_temp=Max('temperature'),
        
        avg_hr=Avg('heart_rate'),
        min_hr=Min('heart_rate'),
        max_hr=Max('heart_rate'),
        
        avg_spo2=Avg('spo2'),
        min_spo2=Min('spo2'),
        max_spo2=Max('spo2'),
        
        avg_sys=Avg('pressure_systolic'),
        min_sys=Min('pressure_systolic'),
        max_sys=Max('pressure_systolic'),
        
        avg_dia=Avg('pressure_diastolic'),
        min_dia=Min('pressure_diastolic'),
        max_dia=Max('pressure_diastolic'),
        
        avg_sugar=Avg('blood_sugar'),
        min_sugar=Min('blood_sugar'),
        max_sugar=Max('blood_sugar'),
        
        avg_weight=Avg('weight'),
        min_weight=Min('weight'),
        max_weight=Max('weight'),
    )
    
    # ===== ДАНІ ДЛЯ ГРАФІКІВ =====
    chart_data = {
        'labels': [r.date.strftime('%d.%m') for r in records],
        
        # Дані
        'temperature': [float(r.temperature) if r.temperature is not None else None for r in records],
        'heart_rate': [r.heart_rate for r in records],
        'spo2': [r.spo2 for r in records],
        'pressure_systolic': [r.pressure_systolic for r in records],
        'pressure_diastolic': [r.pressure_diastolic for r in records],
        'blood_sugar': [float(r.blood_sugar) if r.blood_sugar is not None else None for r in records],
        'weight': [float(r.weight) if r.weight is not None else None for r in records],
        
        # Ризики (для кольорових точок)
        'temperature_risk': [r.temperature_risk for r in records],
        'heart_rate_risk': [r.heart_rate_risk for r in records],
        'spo2_risk': [r.spo2_risk for r in records],
        'pressure_risk': [r.pressure_risk for r in records],
        'blood_sugar_risk': [r.blood_sugar_risk for r in records],
    }
    
    context = {
        'patient': patient,
        'period': period,
        'stats': stats,
        'chart_data': chart_data,
        'records': records,
        'is_doctor_view': patient_id is not None,
    }
    return render(request, 'diary/health_analytics.html', context)
