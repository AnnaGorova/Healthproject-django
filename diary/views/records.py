from django.shortcuts import render, redirect
from ..models import UserProfile, HealthRecord
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from ..forms import HealthRecordForm
from django.http import Http404
from .access import doctor_can_access_patient, get_accessible_patients, is_admin_or_superuser


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
