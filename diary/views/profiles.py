from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from ..forms.user_profile import UserProfileForm
from ..forms.doctor_profile import DoctorProfileForm
from ..models import DoctorProfile


@login_required
def profile(request):
    
    user_profile = request.user.userprofile
   
    
    context = {
        'user_profile': user_profile,
    }
    return render(request, 'diary/profile.html', context)


@login_required
def edit_profile(request):
    user_profile = request.user.userprofile
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=user_profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Профіль оновлено!")
            return redirect('profile')
    else:
        form = UserProfileForm(instance=user_profile)
    
    return render(request, 'diary/edit_profile.html', {
        'user_profile': user_profile,
        'form': form,
    })


@login_required
def edit_doctor_profile(request):
    """Редагування профілю лікаря"""
    user_profile = request.user.userprofile
    
    if user_profile.role != 'doctor':
        raise PermissionDenied("Тільки лікарі можуть редагувати цей профіль")
    
    # Отримуємо або створюємо DoctorProfile
    doctor_profile, created = DoctorProfile.objects.get_or_create(
        user=user_profile,
        defaults={
            'specialty': 'Терапевт',
            'year_of_experience': 0,
            'phone': '',
        }
    )
    
    if request.method == 'POST':
        form = DoctorProfileForm(request.POST, instance=doctor_profile)
        if form.is_valid():
            form.save()
            messages.success(request, "✅ Профіль оновлено")
            return redirect('profile')
    else:
        form = DoctorProfileForm(instance=doctor_profile)
    
    return render(request, 'diary/edit_doctor_profile.html', {
        'form': form,
        'doctor_profile': doctor_profile,
    })
