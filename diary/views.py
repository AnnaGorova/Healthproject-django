from re import search

from django.shortcuts import render, redirect
from django.http import HttpResponse, Http404
from datetime import datetime
from .models import UserProfile, HealthRecord, Medicine
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
    http_method = request.method

    user_profile = request.user.userprofile

    if user_profile.role == 'patient':
        all_records = HealthRecord.objects.filter(user=user_profile)
    else:
        all_records = HealthRecord.objects.all()
    
    
       
    context = {
        'records': all_records,
        'user_profile': user_profile,
       
    }
    
    return render(request, 'diary/records.html', context)


@login_required
def user_records(request, user_id):
    targer_user = get_object_or_404(UserProfile, id=user_id)
    current_user = request.user.userprofile

    if current_user.role == 'patient' and current_user.id != targer_user.id:
        raise PermissionDenied("Ви не маєте доступу до записів іншого користувача")
    
    if current_user.role == 'doctor' and targer_user.role == 'patient':
        if targer_user.doctor != current_user:
            raise PermissionDenied("Отримайте доступ")

    all_records = HealthRecord.objects.filter(user=targer_user)

    context = {
        'records': all_records,
        'user_profile': targer_user,
    }

    return render(request, 'diary/records.html', context)

@login_required
def record_detail(request, pk):
    record = get_object_or_404(HealthRecord, id=pk)
           
    
    context = {
        'record': record,
        'related_medicines': record.medicines.all(),  
        'record_date': record.date
    }

    return render(request, 'diary/record_detail.html', context)

@login_required
def doctor_patients(request, doctor_id):
    doctor = get_object_or_404(UserProfile, id=doctor_id, role='doctor')
    patients = doctor.patients.all()
    context = {
        'doctor' : doctor,
        'patients' : patients,
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
    patients = UserProfile.objects.filter(role='patient')
    doctors = UserProfile.objects.filter(role="doctor")
    admins = UserProfile.objects.filter(role ='admin')
    

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
            context = {
                'data': form.cleaned_data
            }
            return render(request, 'diary/question_sent.html', context)
    else:
        form = DoctorQuestionForm()
    return render(request, 'diary/ask_question.html', {'form': form})



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
    records = HealthRecord.objects.filter(user = user_profile)
    return render(request, 'diary/my_records.html', {'records': records})