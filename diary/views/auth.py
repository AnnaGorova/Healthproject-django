from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.core.validators import validate_email
from django.core.exceptions import ValidationError


def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        # ===== ДОДАТКОВА ПЕРЕВІРКА EMAIL =====
        try:
            validate_email(email)
        except ValidationError:
            messages.error(request, 'Невірний формат email')
            return render(request, 'diary/login.html')


        try:
            user_obj = User.objects.get(email=email)
            
            if not user_obj.is_active:
                messages.error(request, 'Обліковий запис деактивовано. Зверніться до адміністратора.')
                return render(request, 'diary/login.html')
            
            
            user = authenticate(request, username=user_obj.username, password=password)
            
            if user is not None:
                login(request, user)
                return redirect('home')
            else:
                messages.error(request, 'Невірний пароль')
        except User.DoesNotExist:
            messages.error(request, 'Користувача з таким email не знайдено')
    
    return render(request, 'diary/login.html')


def logout_view(request):
    logout(request)
    return redirect('home')
