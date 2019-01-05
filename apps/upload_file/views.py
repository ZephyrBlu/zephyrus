from django.shortcuts import render
from django.http import HttpResponse
from .forms import UploadFileForm

def upload_form(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            # check file(s)
            return # success url
    else:
        form = UploadFileForm()
    return render(request, 'upload.html', {'form': form})