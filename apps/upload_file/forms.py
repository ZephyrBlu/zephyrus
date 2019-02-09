from django import forms


class ReplayFileForm(forms.Form):
    file = forms.FileField()
