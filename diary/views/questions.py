from django.shortcuts import render, redirect
from ..models import Question
from django.shortcuts import get_object_or_404
from ..forms.doctor_question import DoctorQuestionForm
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.core.paginator import Paginator
from django.db.models import Q, OuterRef, Subquery
from django.db.models.functions import Coalesce, Greatest
from ..models import QuestionMessage
from .access import is_admin_or_superuser


@login_required
@require_GET
def question_messages(request, question_id):
    profile = request.user.userprofile
    question = get_object_or_404(
        Question.objects.select_related('patient', 'doctor__user'),
        pk=question_id,
    )
    is_patient = profile.role == 'patient' and question.patient_id == profile.pk
    is_doctor = profile.role == 'doctor' and question.doctor_id == profile.pk
    if is_admin_or_superuser(request.user) or not (is_patient or is_doctor):
        raise PermissionDenied("Ви не маєте доступу до цього діалогу")
    return _question_response(question, patient_view=is_patient)


def _question_response(question, patient_view=False):
    def message_data(message_id, author, text, created_at):
        return {
            'id': message_id,
            'author': author.username,
            'is_doctor': author.role == 'doctor',
            'text': text,
            'date': timezone.localtime(created_at).strftime('%d.%m.%Y %H:%M') if created_at else '',
        }

    dialog = [message_data('initial', question.patient, question.question, question.created_at)]
    if question.answer:
        dialog.append(message_data('legacy-answer', question.doctor, question.answer, question.answered_at))
    for message in question.messages.select_related('author').order_by('created_at', 'pk'):
        dialog.append(message_data(message.pk, message.author, message.text, message.created_at))

    response = JsonResponse({
        'messages': dialog,
        'status': question.status,
        'status_label': 'Очікує відповіді' if patient_view and question.status == 'new' else question.get_status_display(),
        'can_reply': question.status != 'closed' and question.doctor.user.is_active,
        'doctor_active': question.doctor.user.is_active,
        'can_answer': question.status != 'closed',
    })
    response['Cache-Control'] = 'no-store'
    return response


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
        form = DoctorQuestionForm(initial={'phone': user_profile.phone})
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
    
    context = _question_list_context(
        request, Question.objects.filter(patient=user_profile), 'doctor',
    )
    context['patient_view'] = True
    context['status_options'] = [
        ('new', 'Очікують відповіді'),
        ('answered', 'Відповідь надано'),
        ('closed', 'Закриті'),
    ]
    return render(request, 'diary/my_questions.html', context)


@login_required
def all_questions(request):
    # 1. Явна заборона для адмінів
    if is_admin_or_superuser(request.user):
        raise PermissionDenied("Адміністратори не мають доступу до звернень")

    current_user = request.user.userprofile
    
    # 2. Тільки лікар
    if current_user.role != 'doctor':
        raise PermissionDenied("Доступ заборонено")
    
    context = _question_list_context(
        request, Question.objects.filter(doctor=current_user), 'patient',
    )
    return render(request, 'diary/all_questions.html', context)


def _question_list_context(request, questions, counterpart):
    search = request.GET.get('q', '').strip()
    status = request.GET.get('status', '')
    if status not in dict(Question.STATUS_CHOICES):
        status = ''
    latest_message = QuestionMessage.objects.filter(
        question_id=OuterRef('pk'),
    ).order_by('-created_at', '-pk')
    questions = questions.select_related('patient__user', 'doctor__user').annotate(
        latest_text=Subquery(latest_message.values('text')[:1]),
        latest_date=Subquery(latest_message.values('created_at')[:1]),
    ).annotate(
        last_activity=Greatest(
            'created_at',
            Coalesce('answered_at', 'created_at'),
            Coalesce('latest_date', 'created_at'),
        ),
    )
    if search:
        questions = questions.filter(
            Q(**{f'{counterpart}__username__icontains': search})
            | Q(**{f'{counterpart}__user__email__icontains': search})
            | Q(phone__icontains=search)
            | Q(question__icontains=search)
            | Q(answer__icontains=search)
            | Q(messages__text__icontains=search)
        ).distinct()
    if status:
        questions = questions.filter(status=status)
    page = Paginator(questions.order_by('-last_activity', '-pk'), 15).get_page(request.GET.get('page'))
    for question in page:
        question.preview = question.question
        if question.answer:
            question.preview = question.answer
        if question.latest_date:
            question.preview = question.latest_text
    query = request.GET.copy()
    query.pop('page', None)
    return {
        'questions': page,
        'page_obj': page,
        'search': search,
        'selected_status': status,
        'status_options': Question.STATUS_CHOICES,
        'filter_query': query.urlencode(),
    }


@login_required
def answer_question(request, question_id):
    """Відповідь лікаря"""
    
    user_profile = request.user.userprofile
    wants_json = request.headers.get('Accept') == 'application/json'
    
    if user_profile.role != 'doctor':
        raise PermissionDenied("Тільки лікарі можуть відповідати")

    # 1. Знаходимо питання за ID
    question = get_object_or_404(Question, id=question_id)
    
    # 2. Перевіряємо доступ → 403 (замість 404)
    if question.doctor != user_profile:
        raise PermissionDenied("Це питання адресовано іншому лікарю")

    if question.status == 'closed' and request.method == 'POST':
        if wants_json:
            return JsonResponse({'error': 'Це питання закрито'}, status=409)
        messages.error(request, "Це питання закрито")
        return redirect('all_questions')
    
    if request.method == 'POST':
        answer = request.POST.get('answer', '').strip()
        close = request.POST.get('close') == 'on'
        
        if not answer:
            if wants_json:
                return JsonResponse({'error': 'Введіть відповідь'}, status=400)
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
            if wants_json:
                return _question_response(question)

            messages.success(request, "✅ Відповідь надіслано")
            if close:
                return redirect('all_questions')
            return redirect('answer_question', question_id=question.pk)
    
    return render(request, 'diary/answer_question.html', {
        'question': question,
        'answer_draft': request.POST.get('answer', ''),
        'close_checked': request.POST.get('close') == 'on',
    })


@login_required
def reply_question(request, question_id):
    """Пацієнт продовжує діалог"""
    user_profile = request.user.userprofile
    wants_json = request.headers.get('Accept') == 'application/json'
    
    # Тільки пацієнти
    if user_profile.role != 'patient' or is_admin_or_superuser(request.user):
        raise PermissionDenied("Тільки пацієнти можуть відповідати в діалозі")
    

    question = get_object_or_404(
        Question, 
        id=question_id, 
        patient=request.user.userprofile
    )
    
    if request.method == 'POST' and not question.doctor.user.is_active:
        if wants_json:
            return JsonResponse({'error': 'Лікар більше не приймає звернення'}, status=409)
        messages.error(
            request,
            "Лікар більше не приймає звернення. Оберіть іншого лікаря."
        )
        return redirect('my_questions')

    if request.method == 'POST' and question.status == 'closed':
        if wants_json:
            return JsonResponse({'error': 'Це питання закрито'}, status=409)
        messages.error(request, "❌ Це питання закрито")
        return redirect('my_questions')
    
    if request.method == 'POST':
        text = request.POST.get('text', '').strip()
        
        if not text:
            if wants_json:
                return JsonResponse({'error': 'Введіть повідомлення'}, status=400)
            messages.error(request, "⚠️ Введіть повідомлення")
        else:
            QuestionMessage.objects.create(
                question=question,
                author=request.user.userprofile,
                text=text,
            )
            question.status = 'new'  # знову нове
            question.save()
            if wants_json:
                return _question_response(question, patient_view=True)

            messages.success(request, "✅ Повідомлення надіслано")
            return redirect('reply_question', question_id=question.pk)
    
    return render(request, 'diary/answer_question.html', {
        'question': question,
        'patient_view': True,
        'answer_draft': request.POST.get('text', ''),
    })
