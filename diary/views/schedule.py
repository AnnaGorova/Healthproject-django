from django.shortcuts import render, redirect
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from ..models import Appointment, Schedule
from datetime import date, timedelta
from django.db import models
from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from .slots import get_available_slots


@login_required
def manage_schedule(request):
    """Налаштування розкладу лікаря"""
    user_profile = request.user.userprofile
    
    if user_profile.role != 'doctor':
        raise PermissionDenied("Тільки лікарі можуть налаштовувати розклад")
    
    schedules = Schedule.objects.filter(doctor=user_profile).order_by('date', 'start_time')
    today = timezone.localdate()
    selected_period = request.GET.get('period', 'day')
    period_days = {'day': 1, 'week': 7, 'month': 30}
    if selected_period not in (*period_days, 'custom'):
        selected_period = 'day'
    selected_date = today
    period_end = today
    days = period_days.get(selected_period, 1)
    date_error = ''
    date_field = forms.DateField(
        input_formats=['%d.%m.%Y', '%Y-%m-%d'],
        validators=[MinValueValidator(date(1900, 1, 1)), MaxValueValidator(date(9998, 12, 31))],
    )
    try:
        if selected_period == 'custom':
            selected_date = date_field.clean(request.GET.get('date_from'))
            period_end = date_field.clean(request.GET.get('date_to'))
            days = (period_end - selected_date).days + 1
            if days < 1:
                date_error = 'Дата «По» має бути не раніше дати «З».'
            elif days > 366:
                date_error = 'Виберіть період до 366 днів включно.'
        else:
            selected_date = date_field.clean(request.GET.get('date') or today.isoformat())
            period_end = selected_date + timedelta(days=days - 1)
    except ValidationError:
        date_error = 'Заповніть дати у форматі ДД.ММ.РРРР.'

    schedule_days = [] if date_error else get_available_slots(
        user_profile, days=days, start_date=selected_date,
        include_past=True, include_days_off=True, include_completed=True,
    )
    
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
                    slot_duration=30,
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
        'schedule_days': schedule_days,
        'selected_date': selected_date,
        'selected_date_text': request.GET.get('date', '') if date_error and selected_period != 'custom' else selected_date.strftime('%d.%m.%Y'),
        'date_from_text': request.GET.get('date_from', '') if date_error else selected_date.strftime('%d.%m.%Y'),
        'date_to_text': request.GET.get('date_to', '') if date_error else period_end.strftime('%d.%m.%Y'),
        'selected_period': selected_period,
        'period_end': period_end,
        'date_error': date_error,
        'settings_open': request.method == 'POST',
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
