from .views import HomeView
from django.urls import path
from . import views
from .api_views import records_list_api


urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('old_home/', views.old_home, name='old_home'),
    path('about/', views.AboutView.as_view(), name='about'),
    path('records/', views.records, name='records'),
    path('records/create_record/', views.create_record, name='create_record'),
    path('records/my_records/', views.my_records, name='my_records'),
    path('records/<int:user_id>/', views.user_records, name='user_records'),
    path('record_detail/<int:pk>/', views.record_detail, name='record_detail'),
    path('record_detail/<int:pk>/edit_records/', views.edit_record, name='edit_record'),
    path('record/<int:pk>/delete_record/', views.delete_record, name='delete_record'),

    path('doctor/patients/', views.doctor_patients, name='doctor_patients'),
    path('doctor/dashboard/', views.doctor_dashboard, name='doctor_dashboard'),
    path('appointments/doctor/', views.doctor_appointments, name='doctor_appointments'),
    path('doctor/patient/<int:patient_id>/', views.patient_card, name='patient_card'),
    path('doctor/conclusion/<int:appointment_id>/', views.create_conclusion, name='create_conclusion'),
    path('doctor/icd10-autocomplete/', views.icd10_autocomplete, name='icd10-autocomplete'),

    path('profile/doctor/edit/', views.edit_doctor_profile, name='edit_doctor_profile'),
    
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),

    path('doctors/', views.doctors_list, name='doctors_list'),
    path('appointments/book/<int:doctor_id>/', views.book_appointment, name='book_appointment'),
    path('appointments/my/', views.my_appointments, name='my_appointments'),
    path('appointments/cancel/<int:appointment_id>/', views.cancel_appointment, name='cancel_appointment'),
    path('appointments/reschedule/<int:appointment_id>/', views.reschedule_appointment, name='reschedule_appointment'),
    path('appointments/<int:appointment_id>/conclusion/', views.view_conclusion, name='view_conclusion'),
    path('doctor/appointment/<int:appointment_id>/', views.appointment_detail, name='appointment_detail'),
    path('doctor/appointment/<int:appointment_id>/cancel/', views.doctor_cancel_appointment, name='doctor_cancel_appointment'),
    path('doctor/conclusion/<int:conclusion_id>/edit/', views.edit_conclusion, name='edit_conclusion'),


    path('questions/answer/<int:question_id>/', views.answer_question, name='answer_question'),




    path('schedule/', views.manage_schedule, name='manage_schedule'),
    path('schedule/delete/<int:schedule_id>/', views.delete_schedule, name='delete_schedule'),

    
    path('users/', views.users_list, name='users_list'),
    path('ask_question/', views.ask_question, name='ask_question'),
    path('my_questions/', views.my_questions, name='my_questions'),
    path('all_questions/', views.all_questions, name='all_questions'),
    path('questions/reply/<int:question_id>/', views.reply_question, name='reply_question'),
    path('conclusions/my/', views.my_conclusions, name='my_conclusions'),
   
       
   # Адмін-панель
    path('administrator/', views.administrator, name='administrator'),
    path('administrator/users/create/', views.admin_user_create, name='admin_user_create'),
    path('administrator/users/<int:user_id>/edit/', views.admin_user_edit, name='admin_user_edit'),
    path('administrator/users/<int:user_id>/toggle/', views.admin_user_toggle, name='admin_user_toggle'),
   
   
    # api views
    path('api/diary/records/', records_list_api, name='records_list_api'),
    



    ]

