
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from diary import views



class CustomPasswordResetView(auth_views.PasswordResetView):
    """Кастомний PasswordResetView — окремий шаблон для 'Забули пароль?'"""
    email_template_name = 'registration/password_forget.html'
    template_name = 'registration/password_reset_form.html'
    success_url = '/accounts/password_reset/done/'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('diary.urls')),

    # Авторизація (вбудована)
    # path('accounts/', include('django.contrib.auth.urls')),
    # Авторизація — замість include('django.contrib.auth.urls')
    path('accounts/password_reset/', 
         CustomPasswordResetView.as_view(), 
         name='password_reset'),
    path('accounts/password_reset/done/', 
         auth_views.PasswordResetDoneView.as_view(), 
         name='password_reset_done'),
    path('accounts/reset/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(), 
         name='password_reset_confirm'),
    path('accounts/reset/done/', 
         auth_views.PasswordResetCompleteView.as_view(), 
         name='password_reset_complete'),



    # Кастомні views
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    
    ]


