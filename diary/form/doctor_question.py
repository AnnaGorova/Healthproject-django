from django import forms


class DoctorQuestionForm(forms.Form):
    name = forms.CharField(label="Ім'я")
    
    email = forms.EmailField(label="Email")
    phone = forms.CharField(max_length=15, label='Телефон')
  
    question = forms.CharField(label="Питання")

    def clean_question(self):
       
        question = self.cleaned_data.get('question')

        
        if '???' in question:
            return forms.ValidationError('Можна будь-ласка без трьох знаків питання?')

        if len(question) < 10:
            return forms.ValidationError('Питання має містити не менше 10 символів')

        return question