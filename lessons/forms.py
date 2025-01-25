from django import forms
from .models import *

class CourseForm(forms.ModelForm):
    class Meta:
        model = Cours
        fields = ['title', 'description', 'file']
