from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('old_home/', views.old_home, name='old_home'),
    path('records/', views.records, name='records'),
    path('record_detail/<int:pk>/', views.record_detail, name='record_detail'),
    path('medicines/', views.medicines, name='medicines'),
    path('profile/', views.profile, name='profile'),
    path('users/', views.users_list, name='users_list'),
    path('administrator/', views.administrator, name='administrator'),

    ]

