from django import forms
from .models import Replay

class ReplayFileForm(forms.ModelForm):
    class Meta:
        model = Replay
        fields = ['file']
