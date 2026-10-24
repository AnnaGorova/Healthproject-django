from django.shortcuts import render, redirect
from django.views.generic import TemplateView


def old_home(request):
    return redirect('/')


class HomeView(TemplateView):
    def get_template_names(self):
        if self.request.user.is_authenticated:
            return ['diary/home.html']
        return ['diary/landing.html']

    def get_context_data(self, **kwargs):
        """Додає останні заповнені показники пацієнта для карток на головній сторінці."""
        context = super().get_context_data(**kwargs)
        user = self.request.user
        profile = (
            getattr(user, 'userprofile', None)
            if user.is_authenticated else None
        )
        if not profile or profile.role != 'patient' or user.is_superuser:
            return context

        from ..models import HealthRecord

        records = HealthRecord.objects.filter(
            user=profile, is_active=True,
        ).order_by('-date', '-pk')

        temperature = records.filter(temperature__isnull=False).first()
        pulse = records.filter(heart_rate__isnull=False).first()
        pressure = records.filter(
            pressure_systolic__isnull=False,
            pressure_diastolic__isnull=False,
        ).first()
        spo2 = records.filter(spo2__isnull=False).first()
        glucose = records.filter(blood_sugar__isnull=False).first()

        context['health_parameters'] = [
            {
                'label': 'Температура',
                'value': f'{temperature.temperature:g}' if temperature else None,
                'unit': '°C',
                'date': temperature.date if temperature else None,
                'theme': 'mint',
                'icon': 'diary/images/temperature.svg',
            },
            {
                'label': 'Пульс',
                'value': pulse.heart_rate if pulse else None,
                'unit': 'уд/хв',
                'date': pulse.date if pulse else None,
                'theme': 'pink',
                'icon': 'diary/images/pulse.svg',
            },
            {
                'label': 'Артеріальний тиск',
                'value': (
                    f'{pressure.pressure_systolic}/'
                    f'{pressure.pressure_diastolic}'
                    if pressure else None
                ),
                'unit': 'мм рт. ст.',
                'date': pressure.date if pressure else None,
                'theme': 'yellow',
                'icon': 'diary/images/blood-pressure.svg',
            },
            {
                'label': 'SpO₂',
                'value': spo2.spo2 if spo2 else None,
                'unit': '%',
                'date': spo2.date if spo2 else None,
                'theme': 'blue',
                'icon': 'diary/images/spo2.svg',
            },
            {
                'label': 'Глюкоза',
                'value': f'{glucose.blood_sugar:g}' if glucose else None,
                'unit': 'ммоль/л',
                'date': glucose.date if glucose else None,
                'theme': 'purple',
                'icon': 'diary/images/glucose.svg',
            },
        ]
        from datetime import timedelta
        from django.utils import timezone

        periods = {'week': 7, 'month': 30, 'quarter': 90, 'year': 365}
        period = self.request.GET.get('period', 'week')
        if period not in periods:
            period = 'week'
        date_from = timezone.now() - timedelta(days=periods[period])
        chart_records = list(
            records.filter(date__gte=date_from).order_by('date', 'pk')
        )
        context['selected_period'] = period
        context['home_chart_data'] = {
            'labels': [
                timezone.localtime(record.date).strftime('%d.%m %H:%M')
                for record in chart_records
            ],
            'temperature': [record.temperature for record in chart_records],
            'heart_rate': [record.heart_rate for record in chart_records],
            'pressure_systolic': [record.pressure_systolic for record in chart_records],
            'pressure_diastolic': [record.pressure_diastolic for record in chart_records],
            'spo2': [record.spo2 for record in chart_records],
            'blood_sugar': [record.blood_sugar for record in chart_records],
        }
        return context


class AboutView(TemplateView):
    template_name = "diary/about.html"


def custom_404(request, exception):
    """404 Not Found"""
    return render(request, '404.html', status=404)
