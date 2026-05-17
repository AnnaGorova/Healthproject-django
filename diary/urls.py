from .views import HomeView
from django.urls import path
from . import views


urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('old_home/', views.old_home, name='old_home'),
    path('about/', views.AboutView.as_view(), name='about'),
    path('records/', views.records, name='records'),
    path('records/create_record/', views.create_record, name='create_record'),
    path('records/my_records/', views.my_records, name='my_records'),
    path('records/<int:user_id>/', views.user_records, name='user_records'),
    path('record_detail/<int:pk>/', views.record_detail, name='record_detail'),
    path('doctor/<int:doctor_id>/patients/', views.doctor_patients, name='doctor_patients'),
    path('medicines/', views.medicines, name='medicines'),
    path('profile/', views.profile, name='profile'),
    path('users/', views.users_list, name='users_list'),
    path('ask_question/', views.ask_question, name='ask_question'),
    path('administrator/', views.administrator, name='administrator'),
    


    ]

