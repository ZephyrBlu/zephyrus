import hashlib
from django.shortcuts import render, redirect
from .forms import ReplayFileForm
from django.core.validators import FileExtensionValidator
from django.core.files.storage import default_storage
from apps.process_replays.views import parse_replay
from allauth.account.models import EmailAddress
from apps.user_profile.models import BattlenetAccount, Replay


def sha256sum(f):
    h = hashlib.sha256()
    b = bytearray(128 * 1024)
    mv = memoryview(b)
    for n in iter(lambda: f.readinto(mv), 0):
        h.update(mv[:n])
    return h.hexdigest()


def upload_form(request):
    if request.user.is_authenticated and request.method == 'POST':
        form = ReplayFileForm(request.POST, request.FILES)
        replay_files = request.FILES.getlist('file')
        if form.is_valid():
            for file in replay_files:
                file_extension_checker = FileExtensionValidator(['sc2replay'])
                file_extension_checker(file)

                user = request.user

                players, summary_stats, metadata = parse_replay(file)

                if players is None:
                    continue

                player_summary = {}
                player_summary[1] = vars(players[1])
                player_summary[2] = vars(players[2])

                file_hash = sha256sum(file)
                file.name = f'{file_hash}.SC2Replay'
                filename = file.name

                replay_query = Replay.objects.filter(file_hash=file_hash)
                user_account = EmailAddress.objects.get(user=user)
                user_battlenet_accounts = BattlenetAccount.objects.filter(user_account=user_account)

                match_region = players[1].region_id

                duplicate_replay = False
                if replay_query:
                    duplicate_replay = True

                if not duplicate_replay:
                    profile_ids = [players[1].profile_id, players[2].profile_id]
                    kwargs = {f'region_profiles__{match_region}__profile_id__in': profile_ids}
                    if user_battlenet_accounts:
                        player_battlenet_account = user_battlenet_accounts.get(**kwargs)
                    else:
                        player_battlenet_account = None
                    if player_battlenet_account:
                        bucket_path = f'{user.email}/{player_battlenet_account.battletag}/{filename}'

                        player_profile_id = player_battlenet_account.region_profiles[str(match_region)]['profile_id']
                        if players[metadata['winner']].profile_id == player_profile_id:
                            win = True
                        else:
                            win = False
                    else:
                        win = None
                        bucket_path = f'{user.email}/{filename}'

                    replay = Replay(
                        file_hash=file_hash,
                        user_account=user_account,
                        battlenet_account=player_battlenet_account,
                        players=player_summary,
                        match_data=summary_stats,
                        match_length=metadata['game_length'],
                        played_at=metadata['time_played_at'],
                        map=metadata['map'],
                        region_id=match_region,
                        win=win
                    )
                    replay.save()

                    file_contents = file.open(mode='rb')
                    current_replay = default_storage.open(bucket_path, 'w')
                    current_replay.write(file_contents.read())
                    current_replay.close()
                else:
                    # redirect to appropriate replay page
                    pass
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
