import json
from base64 import urlsafe_b64encode, urlsafe_b64decode
from django.shortcuts import render
from apps.user_profile.models import Replay
from apps.api.models import ReplaySerializer


def replay_page(request, base64_url):
    """
    1) get replay info from database
    2) send info to React app
    3) fetch replay timeline
    4) render data
    """

    # 7dd8765d875c5dab9920dd639c0473eb29e507e646a3ff0e9a01708beb7b58a2

    partial_hash = urlsafe_b64decode(bytes(base64_url, 'utf-8')).hex()
    replay_query = Replay.objects.filter(file_hash__startswith=partial_hash)
    serialized_replay = ''

    if replay_query.exists():
        replay = ReplaySerializer(replay_query[0]).data
        for n, info in replay['players'].items():
            info.pop('user_id', None)
            info.pop('realm_id', None)
            info.pop('region_id', None)
            info.pop('profile_id', None)

        new_replay = {}
        for stat, info in replay.items():
            if stat == 'match_data':
                new_replay['match_data'] = {}

                # replace nested dict structure with flat one
                # only resource stats are nested
                for name, values in info.items():
                    if type(values) is dict and 'minerals' in values:
                        for resource, value in values.items():
                            new_replay[stat][f'{name}_{resource}'] = value
                    else:
                        new_replay[stat][name] = values
            else:
                new_replay[stat] = info
        serialized_replay = json.dumps(new_replay)

    return render(request, 'site_structure/replay.html', {
        'replay_data': serialized_replay,
    })
