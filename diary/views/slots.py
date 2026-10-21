from ..models import Appointment, Schedule
from datetime import date, timedelta, time
from django.utils import timezone
from datetime import datetime as dt_class


def is_slot_booked(doctor, slot_start):
    if timezone.is_naive(slot_start):
        slot_start = timezone.make_aware(slot_start)

    duration = timedelta(minutes=30)

    return Appointment.objects.filter(
        doctor=doctor,
        status='scheduled',
        date__gt=slot_start - duration,
        date__lt=slot_start + duration,
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
                    is_booked = is_slot_booked(doctor, current_time)
                    
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
    is_booked = is_slot_booked(doctor, appointment_datetime)
    
    if is_booked:
        return False, "❌ Цей час вже зайнятий"
    
    # 8. Все OK
    return True, None
