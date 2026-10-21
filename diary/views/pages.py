from django.shortcuts import render, redirect
from django.views.generic import TemplateView


def old_home(request):
    return redirect('/')


class HomeView(TemplateView):
    template_name = 'diary/home.html'


class AboutView(TemplateView):
    template_name = "diary/about.html"


def custom_404(request, exception):
    """404 Not Found"""
    return render(request, '404.html', status=404)
