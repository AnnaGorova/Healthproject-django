from django.shortcuts import render, redirect
from .models import UserProfile, HealthRecord, Medicine, Question
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView
from .forms.doctor_question import DoctorQuestionForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from .forms import HealthRecordForm



def old_home(request):
    return redirect('/')


class HomeView(TemplateView):
    template_name = 'diary/home.html'

class AboutView(TemplateView):
    template_name = "diary/about.html" 


@login_required
def records(request):
    user_profile = request.user.userprofile

    if user_profile.role == 'patient':
        all_records = HealthRecord.objects.filter(user=user_profile, is_active=True)
    elif user_profile.role == 'doctor':
        patient_ids = user_profile.patients.values_list('id', flat=True)
        all_records = HealthRecord.objects.filter(user_id__in=patient_ids, is_active=True)
    else:
        all_records = HealthRecord.objects.all()
    
    
       
    context = {
        'records': all_records,
        'user_profile': user_profile,
       
    }
    
    return render(request, 'diary/records.html', context)


@login_required
def user_records(request, user_id):
    target_user = get_object_or_404(UserProfile, id=user_id)
    current_user = request.user.userprofile

    if current_user.role == 'patient' and current_user.id != target_user.id:
        raise PermissionDenied("Ви не маєте доступу до записів іншого користувача")
    
    if current_user.role == 'doctor' and target_user.role == 'patient':
        if target_user.doctor != current_user:
            raise PermissionDenied("Отримайте доступ")

    all_records = HealthRecord.objects.filter(user=target_user, is_active=True)

    context = {
        'records': all_records,
        'user_profile': target_user,
    }

    return render(request, 'diary/records.html', context)

@login_required
def record_detail(request, pk):
    record = get_object_or_404(HealthRecord, id=pk)
    user_profile = request.user.userprofile      
    
    if user_profile.role == 'patient':
        record = get_object_or_404(HealthRecord, id=pk, user=user_profile)
    else: 
        record = get_object_or_404(HealthRecord, id=pk)

    context = {
        'record': record,
        'related_medicines': record.medicines.all(),  
        'record_date': record.date
    }

    return render(request, 'diary/record_detail.html', context)

@login_required
def doctor_patients(request):
    current_user = request.user.userprofile

    if current_user.role not in ['doctor', 'admin']:
        raise PermissionDenied("Ця сторінка доступна тільки для лікаря або адміністратора")
    
    if current_user.role == 'doctor':
        patients = current_user.patients.all()
    else:  
        patients = UserProfile.objects.filter(role='patient')

        

    context = {
        'doctor' : current_user,
        'patients' : patients,
    }
    return render(request, 'diary/doctor_patients.html', context)



def is_doctor(user):
    return user.is_authenticated and user.userprofile.role == 'doctor'

@user_passes_test(is_doctor)
def doctor_dashboard(request):
    doctor = request.user.userprofile
    patients = doctor.patients.all()

    context = {
        'doctor': doctor,
        'patients': patients,
    }

    return render(request, 'diary/doctor_patients.html', context)






@login_required
def medicines(request):
    http_method = request.method
    search = request.GET.get('search', '')
    
    if search:
        medicines_list = Medicine.objects.filter(name__icontains=search)
    else:
        medicines_list = Medicine.objects.all()
   
    context = {
        'medicines': medicines_list,
        'search_query': search,
        'http_method': http_method,
    }
      
    return render(request, 'diary/medicines.html', context)
 


@login_required
def profile(request):
    http_method = request.method

    user_profile = request.user.userprofile
   
    
    context = {
        'user_profile': user_profile,
        'http_method': http_method,
    }
    return render(request, 'diary/profile.html', context)


@login_required   
def users_list(request):
    current_user = request.user.userprofile

    if current_user.role == 'admin':
        patients = UserProfile.objects.filter(role='patient')
        doctors = UserProfile.objects.filter(role="doctor")
        admins = UserProfile.objects.filter(role ='admin')
    elif current_user.role == 'doctor':
        patients = current_user.patients.all()
        doctors = UserProfile.objects.filter(id=current_user.id) 
        admins = []
    else:
        patients = UserProfile.objects.filter(id=current_user.id)
        doctors = UserProfile.objects.filter(role='doctor')
        admins = []

    context = {
        'patients': patients,
        'doctors': doctors,
        'admins': admins,
        'users_count': UserProfile.objects.count(),
    }
    
    return render(request, 'diary/users_list.html', context)     


def is_admin(user):
  return user.is_authenticated and user.userprofile.role == 'admin'   

@user_passes_test(is_admin)
def administrator(request):
    return render(request, 'diary/administrator.html')

@login_required
def ask_question(request):
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
    user_profile = request.user.userprofile
    questions = Question.objects.filter(patient=user_profile).order_by('-created_at')
    return render(request, 'diary/my_questions.html', {'questions': questions})



@login_required
def all_questions(request):
    current_user = request.user.userprofile
    
    if current_user.role not in ['doctor', 'admin']:
        raise PermissionDenied("Доступ заборонено")
    
    questions = Question.objects.all().order_by('-created_at')
    
    context = {
        'questions': questions,
    }
    return render(request, 'diary/all_questions.html', context)



@login_required
def create_record(request):
    if request.method == 'POST':
        form = HealthRecordForm(request.POST)
        if form.is_valid():
            record = form.save(commit=False)
            record.user = request.user.userprofile
            record.save()
            form.save_m2m() #для збереження ліків

            messages.success(request, "Запис в щоденнику успішно створений!")
            return redirect('records')
    else:
        form = HealthRecordForm()
    return render (request, 'diary/create_record.html', {'form': form})
        

@login_required
def my_records(request):
    user_profile = request.user.userprofile
    records = HealthRecord.objects.filter(user = user_profile, is_active=True)
    return render(request, 'diary/my_records.html', {'records': records})




@login_required
def edit_record(request, pk):
    record = get_object_or_404(HealthRecord, id=pk)
    current_user = request.user.userprofile

   
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
   
    if record.user != request.user.userprofile:
        raise PermissionDenied("Ви не можете видалити чужий запис")
    
    if request.method == 'POST':
        record.delete()
        messages.success(request, "Запис успішно видалено!")
        return redirect('my_records')
    
    return render(request, 'diary/delete_record.html', {'record': record})







