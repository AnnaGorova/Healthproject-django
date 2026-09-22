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

    
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),

    path('doctors/', views.doctors_list, name='doctors_list'),
    path('appointments/book/<int:doctor_id>/', views.book_appointment, name='book_appointment'),
    path('appointments/my/', views.my_appointments, name='my_appointments'),
    path('appointments/cancel/<int:appointment_id>/', views.cancel_appointment, name='cancel_appointment'),
    path('appointments/reschedule/<int:appointment_id>/', views.reschedule_appointment, name='reschedule_appointment'),
    path('questions/answer/<int:question_id>/', views.answer_question, name='answer_question'),




    path('schedule/', views.manage_schedule, name='manage_schedule'),
    path('schedule/delete/<int:schedule_id>/', views.delete_schedule, name='delete_schedule'),

    
    path('users/', views.users_list, name='users_list'),
    path('ask_question/', views.ask_question, name='ask_question'),
    path('my_questions/', views.my_questions, name='my_questions'),
    path('all_questions/', views.all_questions, name='all_questions'),
    path('questions/reply/<int:question_id>/', views.reply_question, name='reply_question'),

   
    path('administrator/', views.administrator, name='administrator'),
    # api views
    path('api/diary/records/', records_list_api, name='records_list_api'),
    



    ]

