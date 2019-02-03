from django.shortcuts import render
from apps.upload_file.models import ReplayInfo
from .models import ReplaySerializer
from django.http import JsonResponse
from rest_framework.renderers import JSONRenderer

def return_replay_data(request):
    if request.method == 'GET':
        replay_data = ReplayInfo.objects.latest('uploaded_at')
        serializer = ReplaySerializer(replay_data)
        return JsonResponse(serializer.data, safe=False)
