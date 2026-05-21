from django import forms
from ..models import Question   

class DoctorQuestionForm(forms.ModelForm):
    class Meta: 
        model = Question
        fields = ['phone', 'question']

        
    def clean_question(self):
       
        question = self.cleaned_data.get('question')

        
        if '???' in question:
            raise forms.ValidationError('Можна будь-ласка без трьох знаків питання?')

        if len(question) < 10:
            raise forms.ValidationError('Питання має містити не менше 10 символів')

        return question