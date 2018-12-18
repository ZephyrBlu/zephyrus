from django.shortcuts import render
from django.http import HttpResponse

def upload_form(request, context):
    return render(request, 'upload_file/upload_form.html', context)