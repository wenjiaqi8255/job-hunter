from django import forms
from .models import SavedJob

class SavedJobForm(forms.ModelForm):
    class Meta:
        model = SavedJob
        fields = ['status', 'notes']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select mb-3'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        } 