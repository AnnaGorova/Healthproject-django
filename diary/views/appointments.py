from django.shortcuts import render, redirect
from ..models import UserProfile
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from ..models import Appointment
from django.db.models import Q, Count
from datetime import datetime as dt_class
from .access import is_admin_or_superuser
from .slots import get_available_slots, is_slot_available


@login_required
def book_appointment(request, doctor_id):
    """Запис до конкретного лікаря"""
    doctor = get_object_or_404(
        UserProfile, id=doctor_id, role='doctor', user__is_active=True
    )
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
