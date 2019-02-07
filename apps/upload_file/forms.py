from django import forms
# from .models import Replay


class ReplayFileForm(forms.Form):
    file = forms.FileField()
