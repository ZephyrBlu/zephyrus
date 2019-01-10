from django.shortcuts import render
from apps.upload_file.models import Replay
from apps.processreplays.views import parse_replay


def display_replay(request, context):
    replay = Replay.objects.latest('uploaded_at')
    summary_info = parse_replay(replay.file)
    for k, player in summary_info.items():
        context[f'{k}'] = player['workers_produced']
    return render(request, 'user_profile/profile.html', context)
