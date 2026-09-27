from django import forms
from dal import autocomplete
from diary.models import MedicalConclusion


class MedicalConclusionForm(forms.ModelForm):
    class Meta:
        model = MedicalConclusion
        fields = ['icd10', 'diagnosis', 'prescriptions', 'recommendations']
        widgets = {
            'icd10': autocomplete.Select2(
                url='icd10-autocomplete',
                attrs={
                    'data-placeholder': 'Почніть вводити код або назву діагнозу...',
                    'data-minimum-input-length': 2,
                    'style': 'width: 100%;',
                },
            ),
            'diagnosis': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'prescriptions': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'recommendations': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
        }
        labels = {
            'icd10': 'Шифр МКХ-10',
            'diagnosis': 'Діагноз (текстом)',
            'prescriptions': 'Призначення',
            'recommendations': 'Рекомендації',
        }