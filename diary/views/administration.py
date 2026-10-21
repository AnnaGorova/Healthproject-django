from django.shortcuts import render, redirect
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.contrib.auth.models import User
from django.db import models
from ..models import DoctorProfile
import re
from .profiles import profile


@login_required
def administrator(request):
    """Кастомна сторінка адміністратора"""
    user_profile = request.user.userprofile
    
    if user_profile.role != 'admin':
        raise PermissionDenied("Тільки адміністратори мають доступ")
    
    users = User.objects.select_related('userprofile').order_by('-id')
    
    # Пошук
    search = request.GET.get('search', '').strip()
    if search:
        users = users.filter(
            models.Q(username__icontains=search) |
            models.Q(email__icontains=search) |
            models.Q(userprofile__username__icontains=search)
        )
    
    # Фільтр за роллю
    role = request.GET.get('role', '').strip()
    if role:
        users = users.filter(userprofile__role=role)
    
    return render(request, 'diary/administrator.html', {
        'users': users,
        'search': search,
        'role': role,
    })


@login_required
def admin_user_create(request):
    """Створення користувача адміном"""
    user_profile = request.user.userprofile
    
    if user_profile.role != 'admin':
        raise PermissionDenied("Тільки адміністратори мають доступ")
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        middle_name = request.POST.get('middle_name', '').strip()
        role = request.POST.get('role', 'patient')
        phone = request.POST.get('phone', '').strip()
        gender = request.POST.get('gender', '').strip()          
        date_of_birth = request.POST.get('date_of_birth', '').strip()  
        
        # Валідація
        if not username or not email:
            messages.error(request, "⚠️ Логін і email обов'язкові")
        elif User.objects.filter(username=username).exists():
            messages.error(request, "⚠️ Такий логін вже існує")
        elif User.objects.filter(email=email).exists():
            messages.error(request, "⚠️ Такий email вже існує")
        elif phone and not re.match(r'^\+?[\d\s\-\(\)]{10,20}$', phone): 
            messages.error(request, "⚠️ Некоректний телефон. Приклад: +380501234567")
        else:
            # Створення User (без пароля → сигнал надішле лист)
            user = User.objects.create_user(
                username=username,
                email=email,
                password=None,
            )
            user.first_name = first_name
            user.last_name = last_name
            user.save()
            
            # UserProfile створюється сигналом, але роль і телефон треба оновити
            profile = user.userprofile
            profile.role = role
            profile.phone = phone
            profile.middle_name = middle_name
            profile.username = f"{last_name} {first_name} {middle_name}".strip() or username
            
            
            if gender:
                profile.gender = gender
            if date_of_birth:
                profile.date_of_birth = date_of_birth
            
            profile.save()
            
            # Якщо лікар — створити DoctorProfile
            if role == 'doctor':
                DoctorProfile.objects.get_or_create(
                    user=profile,
                    defaults={
                        'specialty': 'Терапевт',
                        'year_of_experience': 0,
                        'phone': '',
                    }
                )
            
            messages.success(request, f"✅ Користувача {username} створено, лист надіслано")
            return redirect('administrator')
    
    return render(request, 'diary/admin_user_form.html', {
        'action': 'create',
    })


@login_required
def admin_user_edit(request, user_id):
    """Редагування користувача адміном"""
    user_profile = request.user.userprofile
    
    if user_profile.role != 'admin':
        raise PermissionDenied("Тільки адміністратори мають доступ")
    
    user = get_object_or_404(User, id=user_id)
    profile = user.userprofile
    
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        middle_name = request.POST.get('middle_name', '').strip()
        role = request.POST.get('role', 'patient')
        phone = request.POST.get('phone', '').strip()
        gender = request.POST.get('gender', '').strip()
        date_of_birth = request.POST.get('date_of_birth', '').strip()

        # ===== ВАЛІДАЦІЯ ТЕЛЕФОНУ =====
        if phone and not re.match(r'^\+?[\d\s\-\(\)]{10,20}$', phone):
            messages.error(request, "⚠️ Некоректний телефон. Приклад: +380501234567")
            return render(request, 'diary/admin_user_form.html', {    # ← ОСЬ ЦЕ ДОДАТИ!
                'action': 'edit',
                'user_obj': user,
                'profile': profile,
            })
        
        # Перевірка email (крім свого)
        if User.objects.filter(email=email).exclude(id=user.id).exists():
            messages.error(request, "⚠️ Такий email вже існує")
        else:
            user.email = email
            user.first_name = first_name
            user.last_name = last_name
            user.save()
            
            profile.role = role
            profile.phone = phone
            profile.middle_name = middle_name 
            profile.username = f"{last_name} {first_name} {middle_name}".strip() or user.username
            
            if gender:
                profile.gender = gender
            if date_of_birth:
                profile.date_of_birth = date_of_birth
            
            profile.save()
            
            if role == 'doctor':
                DoctorProfile.objects.get_or_create(
                    user=profile,
                    defaults={
                        'specialty': 'Терапевт',
                        'year_of_experience': 0,
                        'phone': '',
                    }
                )
            
            messages.success(request, "✅ Користувача оновлено")
            return redirect('administrator')
    
    return render(request, 'diary/admin_user_form.html', {
        'action': 'edit',
        'user_obj': user,
        'profile': profile,
    })


@login_required
def admin_user_toggle(request, user_id):
    """Деактивація / активація користувача"""
    user_profile = request.user.userprofile
    
    if user_profile.role != 'admin':
        raise PermissionDenied("Тільки адміністратори мають доступ")

    #  ТІЛЬКИ POST!
    if request.method != 'POST':
        messages.error(request, "❌ Некоректний метод запиту")
        return redirect('administrator')
    
    user = get_object_or_404(User, id=user_id)
    
    # Не можна деактивувати себе
    if user.id == request.user.id:
        messages.error(request, "❌ Не можна деактивувати себе")
        return redirect('administrator')
    
    # Не можна деактивувати superuser
    if user.is_superuser:
        messages.error(request, "❌ Не можна деактивувати суперкористувача")
        return redirect('administrator')
    
    user.is_active = not user.is_active
    user.save()
    
    status = "активовано" if user.is_active else "деактивовано"
    messages.success(request, f"✅ Користувача {user.username} {status}")
    return redirect('administrator')
