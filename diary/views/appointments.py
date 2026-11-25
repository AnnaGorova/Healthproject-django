from django.shortcuts import render, redirect
from ..models import UserProfile
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.contrib import messages
from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils import timezone
from django.urls import Resolver404, resolve, reverse
from django.utils.http import url_has_allowed_host_and_scheme
from urllib.parse import urlsplit
from ..models import Appointment
from django.db.models import Q, Count
from datetime import date, datetime as dt_class, timedelta
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
    
    # Показуємо сім календарних днів від обраної дати або від сьогодні.
    today = timezone.localdate()
    selected_date_text = request.GET.get('start_date', '').strip() or today.strftime('%d.%m.%Y')
    date_field = forms.DateField(
        input_formats=['%d.%m.%Y', '%Y-%m-%d'],
        validators=[MinValueValidator(today), MaxValueValidator(date(9998, 12, 31))],
    )
    date_error = ''
    period_end = None
    slots = []
    try:
        selected_date = date_field.clean(selected_date_text)
        selected_date_text = selected_date.strftime('%d.%m.%Y')
        period_end = selected_date + timedelta(days=6)
        slots = get_available_slots(doctor, days=7, start_date=selected_date, include_days_off=True)
    except ValidationError:
        date_error = 'Вкажіть дату у форматі ДД.ММ.РРРР, не раніше сьогоднішньої.'
    
    return render(request, 'diary/book_appointment.html', {
        'doctor': doctor,
        'slots': slots,
        'selected_date_text': selected_date_text,
        'period_end': period_end,
        'date_error': date_error,
        'today': today,
        'has_available_slots': any(not slot['is_booked'] for day in slots for slot in day['slots']),
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
    ).select_related('doctor__doctor_profile', 'cancelled_by', 'conclusion__icd10')

    appointments, current_status, counts = filter_appointments(request, appointments)

    # Однакові дати впорядковуємо за ID, щоб записи не повторювалися між сторінками.
    descending = current_status != 'active'
    appointments = appointments.order_by('-date' if descending else 'date', '-pk' if descending else 'pk')
    appointments_page = Paginator(appointments, 10).get_page(request.GET.get('page'))

    return render(request, 'diary/my_appointments.html', {
        'appointments': appointments_page.object_list,
        'appointments_page': appointments_page,
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
    ).select_related('patient', 'cancelled_by', 'conclusion')

    appointments, current_status, counts = filter_appointments(request, appointments)

    descending = current_status != 'active'
    appointments = appointments.order_by('-date' if descending else 'date', '-pk' if descending else 'pk')
    appointments_page = Paginator(appointments, 10).get_page(request.GET.get('page'))

    return render(request, 'diary/doctor_appointments.html', {
        'appointments': appointments_page.object_list,
        'appointments_page': appointments_page,
        'current_status': current_status,
        'counts': counts,
    })


def _doctor_appointment_back_url(request):
    sources = {'doctor_appointments', 'doctor_dashboard', 'patient_card', 'manage_schedule'}
    params = request.POST if request.method == 'POST' else request.GET
    for candidate in (params.get('next', ''), request.META.get('HTTP_REFERER', '')):
        if not candidate or not url_has_allowed_host_and_scheme(
            candidate, allowed_hosts={request.get_host()}, require_https=request.is_secure()
        ):
            continue
        try:
            route = resolve(urlsplit(candidate).path)
        except Resolver404:
            continue
        if route.url_name in sources:
            return candidate
    return reverse('doctor_appointments')


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
        'back_url': _doctor_appointment_back_url(request),
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

    back_url = _doctor_appointment_back_url(request)
    detail_url = reverse('appointment_detail', args=[appointment.id], query={'next': back_url})

    if appointment.status != 'scheduled':
        messages.error(request, "❌ Цей прийом вже не активний")
        return redirect(detail_url)

    if request.method == 'POST':
        appointment.status = 'cancelled'
        appointment.cancelled_by = user_profile
        appointment.save()
        messages.success(request, "✅ Прийом скасовано")
        return redirect(back_url)

    return render(request, 'diary/doctor_cancel_confirm.html', {
        'appointment': appointment,
        'back_url': back_url,
        'detail_url': detail_url,
    })
