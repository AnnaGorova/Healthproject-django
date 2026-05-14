from re import search

from django.shortcuts import render, redirect
from django.http import HttpResponse, Http404
from datetime import datetime
from .models import UserProfile, HealthRecord, Medicine
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView
from .form.doctor_question import DoctorQuestionForm

def old_home(request):
    return redirect('/')


def home(request):
    user = UserProfile.objects.filter(id=1).first()
    records_count = HealthRecord.objects.filter(user=user).count() if user else 0

    context = {
        'records_count': records_count,
        'user': user,
    }

    return render(request, 'diary/home.html', context)

class AboutView(TemplateView):
    template_name = "diary/about.html" 



def records(request):
    http_method = request.method


    user = UserProfile.objects.get(id=1)
    all_records = HealthRecord.objects.filter(user=user)
       
    context = {
        'records': all_records,
        'user': user,
       
    }
    
    return render(request, 'diary/records.html', context)

def user_records(request, user_id):
    user = get_object_or_404(UserProfile, id=user_id)
    all_records = HealthRecord.objects.filter(user=user)

    context = {
        'records': all_records,
        'user': user,
    }

    return render(request, 'diary/records.html', context)

def record_detail(request, pk):
    record = get_object_or_404(HealthRecord, id=pk)
           
    
    context = {
        'record': record,
        'related_medicines': record.medicines.all(),  
        'record_date': record.date
    }

    return render(request, 'diary/record_detail.html', context)


def doctor_patients(request, doctor_id):
    doctor = get_object_or_404(UserProfile, id=doctor_id, role='doctor')
    patients = doctor.patients.all()
    context = {
        'doctor' : doctor,
        'patients' : patients,
    }
    return render(request, 'diary/doctor_patients.html', context)

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
 


def profile(request):
    http_method = request.method

    user = UserProfile.objects.filter(id=1).first()
    if not user:
        user = UserProfile.objects.create(
            username="Olga Ivanova", 
            email="olga_I@gmail.com", 
            role="patient") 
    
    context = {
        'user': user,
        'http_method': http_method,
    }
    return render(request, 'diary/profile.html', context)
   
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




def administrator(request):
    return render(request, 'diary/administrator.html')


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


