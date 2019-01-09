from django.shortcuts import render
from apps.upload_file.models import Replay
from apps.processreplays.views import parse_replay

def display_replay(request, context):
    replay = Replay.objects.latest('uploaded_at')
    context['info'] = parse_replay(replay.file)
    return render(request, 'user_profile/profile.html', context)
