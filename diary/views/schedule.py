from django.shortcuts import render, redirect
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from ..models import Appointment, Schedule
from datetime import date
from django.db import models


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
