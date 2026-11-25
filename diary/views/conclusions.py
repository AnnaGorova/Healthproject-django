from django.shortcuts import render, redirect
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from ..models import Appointment
from django.utils import timezone
from ..models import MedicalConclusion
from ..models import ICD10Code
from django.http import JsonResponse
from django.db.models import Q
from django.urls import Resolver404, resolve, reverse
from django.utils.http import url_has_allowed_host_and_scheme
from urllib.parse import urlsplit
from ..forms.conclusion import MedicalConclusionForm


@login_required
def create_conclusion(request, appointment_id):
    """Створення висновку після прийому"""
    user_profile = request.user.userprofile

    if user_profile.role != 'doctor':
        raise PermissionDenied("Тільки лікарі можуть створювати висновки")

    appointment = get_object_or_404(
        Appointment,
        id=appointment_id,
        doctor=user_profile
    )
    # Перевірка: чи прийом уже відбувся
    if appointment.date > timezone.now():
        messages.error(request, "⚠️ Не можна створити висновок до початку прийому")
        return redirect('patient_card', patient_id=appointment.patient.id)

    # Перевірка: чи вже є висновок
    if hasattr(appointment, 'conclusion'):
        messages.warning(request, "⚠️ Висновок вже створено")
        return redirect('patient_card', patient_id=appointment.patient.id)

    # Перевірка: чи прийом не скасовано
    if appointment.status == 'cancelled':
        messages.error(request, "❌ Не можна створити висновок для скасованого прийому")
        return redirect('patient_card', patient_id=appointment.patient.id)


    if request.method == 'POST':
        form = MedicalConclusionForm(request.POST)
        if form.is_valid():
            conclusion = form.save(commit=False)
            conclusion.appointment = appointment
            conclusion.doctor = user_profile
            conclusion.patient = appointment.patient
            conclusion.save()

            appointment.status = 'completed'
            appointment.save()

            messages.success(request, "✅ Висновок створено")
            return redirect('patient_card', patient_id=appointment.patient.id)
    else:
        form = MedicalConclusionForm()

    return render(request, 'diary/create_conclusion.html', {
        'appointment': appointment,
        'form': form,
        'back_url': _conclusion_back_url(request, appointment, user_profile.role),
    })


def _conclusion_back_url(request, appointment, role):
    if role == 'patient':
        sources = {'my_appointments', 'my_conclusions'}
        fallback = reverse('my_appointments')
    else:
        sources = {'appointment_detail', 'doctor_appointments', 'doctor_dashboard', 'patient_card'}
        fallback = reverse('appointment_detail', args=[appointment.id])

    for candidate in (request.GET.get('next', ''), request.META.get('HTTP_REFERER', '')):
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
    return fallback


@login_required
def view_conclusion(request, appointment_id):
    """Перегляд висновку пацієнтом"""
    user_profile = request.user.userprofile
    
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    # Перевірка: пацієнт — власник, або лікар цього прийому
    if user_profile.role == 'patient':
        if appointment.patient != user_profile:
            raise PermissionDenied("Це не ваш прийом")
    elif user_profile.role == 'doctor':
        if appointment.doctor != user_profile:
            raise PermissionDenied("Це не ваш прийом")
    else:
        raise PermissionDenied("Доступ заборонено")
    
    back_url = _conclusion_back_url(request, appointment, user_profile.role)
    # Перевірка: чи є висновок
    if not hasattr(appointment, 'conclusion'):
        messages.error(request, "❌ Висновок ще не створено")
        return redirect(back_url)

    return render(request, 'diary/view_conclusion.html', {
        'appointment': appointment,
        'conclusion': appointment.conclusion,
        'back_url': back_url,
        'back_to_conclusions': (
            user_profile.role == 'patient'
            and urlsplit(back_url).path == reverse('my_conclusions')
        ),
    })


@login_required
def my_conclusions(request):
    """Всі висновки пацієнта"""
    user_profile = request.user.userprofile
    
    if user_profile.role != 'patient':
        raise PermissionDenied("Тільки пацієнти можуть бачити цю сторінку")
    
    conclusions = MedicalConclusion.objects.filter(
        patient=user_profile
    ).select_related('doctor', 'appointment').order_by('created_at')
    
    return render(request, 'diary/my_conclusions.html', {
        'conclusions': conclusions,
    })


@login_required
def icd10_autocomplete(request):
    """Пошук кодів МКХ-10 за кодом або назвою (JSON)"""
    user_profile = getattr(request.user, 'userprofile', None)

    if not user_profile or user_profile.role != 'doctor':
        return JsonResponse({'results': [], 'pagination': {'more': False}})

    q = request.GET.get('q', '').strip()

    qs = ICD10Code.objects.all()
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(code__istartswith=q)).distinct()

    qs = qs.order_by('code')[:50]

    results = [
        {'id': item.id, 'text': f"{item.code} — {item.name}"}
        for item in qs
    ]

    return JsonResponse({
        'results': results,
        'pagination': {'more': False},
    })


@login_required
def edit_conclusion(request, conclusion_id):
    """Редагування вже створеного висновку"""
    user_profile = request.user.userprofile

    if user_profile.role != 'doctor':
        raise PermissionDenied("Тільки лікарі можуть редагувати висновки")

    conclusion = get_object_or_404(
        MedicalConclusion,
        id=conclusion_id,
        doctor=user_profile
    )
    back_url = _conclusion_back_url(request, conclusion.appointment, user_profile.role)

    if request.method == 'POST':
        form = MedicalConclusionForm(request.POST, instance=conclusion)
        if form.is_valid():
            form.save()
            messages.success(request, "✅ Висновок оновлено")
            return redirect(reverse('view_conclusion', args=[conclusion.appointment.id], query={'next': back_url}))
    else:
        form = MedicalConclusionForm(instance=conclusion)

    return render(request, 'diary/edit_conclusion.html', {
        'form': form,
        'conclusion': conclusion,
        'back_url': back_url,
    })
