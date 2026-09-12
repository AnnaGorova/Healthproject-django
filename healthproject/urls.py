
from django.contrib import admin

from django.urls import path, include
from diary import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('diary.urls')),


    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    ]


