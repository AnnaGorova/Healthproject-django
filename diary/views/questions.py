from django.shortcuts import render, redirect
from ..models import Question
from django.shortcuts import get_object_or_404
from ..forms.doctor_question import DoctorQuestionForm
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.utils import timezone
from ..models import QuestionMessage
from .access import is_admin_or_superuser


@login_required
def ask_question(request):
    user_profile = request.user.userprofile
       
    # Тільки пацієнти
    if user_profile.role != 'patient':
        raise PermissionDenied("Тільки пацієнти можуть задавати питання")

    if request.method == 'POST':
        form = DoctorQuestionForm(request.POST)
        if form.is_valid():
            question = form.save(commit=False)
            question.patient = request.user.userprofile 
            question.save()
            return render(request, 'diary/question_sent.html', {
                'data': form.cleaned_data,
                'user_profile': request.user.userprofile,
            })
    else:
        form = DoctorQuestionForm()
    return render(request, 'diary/ask_question.html', {'form': form})


@login_required  
def my_questions(request):
    # Заборона для адмінів
    if is_admin_or_superuser(request.user):
        raise PermissionDenied("Адміністратори не мають доступу")
    
    user_profile = request.user.userprofile
    # Тільки пацієнти
    if user_profile.role != 'patient':
        raise PermissionDenied("Тільки пацієнти можуть бачити свої питання")
    
    questions = Question.objects.filter(patient=user_profile).order_by('-created_at')
    return render(request, 'diary/my_questions.html', {'questions': questions})


@login_required
def all_questions(request):
    # 1. Явна заборона для адмінів
    if is_admin_or_superuser(request.user):
        raise PermissionDenied("Адміністратори не мають доступу до звернень")

    current_user = request.user.userprofile
    
    # 2. Тільки лікар
    if current_user.role != 'doctor':
        raise PermissionDenied("Доступ заборонено")
    
    # 3. Тільки свої звернення
    questions = Question.objects.filter(doctor=current_user).order_by('-created_at')
    
    return render(request, 'diary/all_questions.html', {
        'questions': questions,
    })


@login_required
def answer_question(request, question_id):
    """Відповідь лікаря"""
    
    user_profile = request.user.userprofile
    
    if user_profile.role != 'doctor':
        raise PermissionDenied("Тільки лікарі можуть відповідати")

    # 1. Знаходимо питання за ID
    question = get_object_or_404(Question, id=question_id)
    
    # 2. Перевіряємо доступ → 403 (замість 404)
    if question.doctor != user_profile:
        raise PermissionDenied("Це питання адресовано іншому лікарю")
    
    if request.method == 'POST':
        answer = request.POST.get('answer', '').strip()
        close = request.POST.get('close') == 'on'
        
        if not answer:
            messages.error(request, "⚠️ Введіть відповідь")
        else:
            # Створюємо повідомлення
            QuestionMessage.objects.create(
                question=question,
                author=user_profile,
                text=answer,
            )
            
            question.doctor = user_profile
            question.answered_at = timezone.now()
            question.status = 'closed' if close else 'answered'
            question.save()
            
            messages.success(request, "✅ Відповідь надіслано")
            return redirect('all_questions')
    
    return render(request, 'diary/answer_question.html', {
        'question': question,
    })


@login_required
def reply_question(request, question_id):
    """Пацієнт продовжує діалог"""
    user_profile = request.user.userprofile
    
    # Тільки пацієнти
    if user_profile.role != 'patient':
        raise PermissionDenied("Тільки пацієнти можуть відповідати в діалозі")
    

    question = get_object_or_404(
        Question, 
        id=question_id, 
        patient=request.user.userprofile
    )
    
    if not question.doctor.user.is_active:
        messages.error(
            request,
            "Лікар більше не приймає звернення. Оберіть іншого лікаря."
        )
        return redirect('my_questions')

    if question.status == 'closed':
        messages.error(request, "❌ Це питання закрито")
        return redirect('my_questions')
    
    if request.method == 'POST':
        text = request.POST.get('text', '').strip()
        
        if not text:
            messages.error(request, "⚠️ Введіть повідомлення")
        else:
            QuestionMessage.objects.create(
                question=question,
                author=request.user.userprofile,
                text=text,
            )
            question.status = 'new'  # знову нове
            question.save()
            
            messages.success(request, "✅ Повідомлення надіслано")
            return redirect('my_questions')
    
    return render(request, 'diary/reply_question.html', {
        'question': question,
    })
