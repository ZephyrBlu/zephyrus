import hashlib
from django.shortcuts import render, redirect
from .forms import ReplayFileForm
from django.core.validators import FileExtensionValidator
from django.core.files.storage import default_storage
from apps.processreplays.views import parse_replay
from .models import ReplayInfo
from allauth.account.models import EmailAddress
from apps.user_profile.models import BattlenetAccount


def sha256sum(f):
    h = hashlib.sha256()
    b = bytearray(128 * 1024)
    mv = memoryview(b)
    for n in iter(lambda: f.readinto(mv), 0):
        h.update(mv[:n])
    return h.hexdigest()


def upload_form(request):
    if request.method == 'POST':
        form = ReplayFileForm(request.POST, request.FILES)
        replay_files = request.FILES.getlist('file')
        if form.is_valid():
            for file in replay_files:
                file_extension_checker = FileExtensionValidator(['sc2replay'])
                file_extension_checker(file)

                user = request.user

                errors, meta_data, player_info, summary_info = parse_replay(file)
                if errors is not None:
                    # error has occurred during parsing
                    pass

                file_hash = sha256sum(file)
                file.name = f'{file_hash}.SC2Replay'
                filename = file.name

                user_info = None
                opponent_info = None
                user_battlenet = BattlenetAccount.objects.get(user_account=EmailAddress.objects.get(user=user))
                for player, info in player_info.items():
                    if info['battlenet_id'] == user_battlenet.id:
                        user_info = summary_info[player]
                    else:
                        opponent_info = summary_info[player]

                bucket_path = f'{user.email}/{user_battlenet.battletag}/{filename}'
                query_for_replay = ReplayInfo.objects.filter(file_hash=file_hash)

                if query_for_replay:
                    # replay already uploaded
                    # request.session['file_hash'] = file_hash
                    pass
                else:
                    replay = ReplayInfo(file_hash=file_hash,
                                        battlenet_account=user_battlenet,
                                        user=user_info,
                                        opponent=opponent_info,
                                        played_at=meta_data['time_played_at'],
                                        game_map=meta_data['game_map']
                                        )
                    replay.save()

                    file_contents = file.open(mode='rb')
                    current_replay = default_storage.open(bucket_path, 'w')
                    current_replay.write(file_contents.read())
                    current_replay.close()
            return redirect('/profile/')
    else:
        info = 'This is the upload page'
        heading = 'Upload'
        title = 'Zephyrus | Upload'
        active = 'upload'
        context = {
            'info': info,
            'heading': heading,
            'title': title,
            'active': active
        }

        form = ReplayFileForm()
        context['form'] = form
    return render(request, 'upload_file/upload.html', context)
