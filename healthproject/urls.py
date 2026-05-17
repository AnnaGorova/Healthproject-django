
from django.contrib import admin
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('diary.urls')),
    path('login/', LoginView.as_view(template_name="diary/login.html"), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    
    ]


