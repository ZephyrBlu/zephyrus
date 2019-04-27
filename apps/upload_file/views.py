import hashlib
from django.shortcuts import render, redirect
from .forms import ReplayFileForm
from django.core.validators import FileExtensionValidator
from django.core.files.storage import default_storage
from apps.processreplays.views import parse_replay
from allauth.account.models import EmailAddress
from apps.user_profile.models import BattlenetAccount, AuthenticatedReplay, UnauthenticatedReplay


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

                # user_info = None
                # opponent_info = None
                uploaded = False
                auth_replay_query = AuthenticatedReplay.objects.filter(file_hash=file_hash)
                unauth_replay_query = UnauthenticatedReplay.objects.filter(file_hash=file_hash)

                if not auth_replay_query and not unauth_replay_query:
                    user_battlenet_accounts = BattlenetAccount.objects.filter(user_account=EmailAddress.objects.get(user=user))
                    for account in user_battlenet_accounts:
                        if account.battletag in player_info:
                            bucket_path = f'{user.email}/{account.battletag}/{filename}'

                            user_in_game_name = None
                            opponent_in_game_name = None
                            for battletag, in_game_name in player_info.items():
                                if battletag == account.battletag:
                                    user_in_game_name = in_game_name
                                else:
                                    opponent_in_game_name = in_game_name

                            replay = AuthenticatedReplay(
                                file_hash=file_hash,
                                battlenet_account=account,
                                user_in_game_name=user_in_game_name,
                                opponent_in_game_name=opponent_in_game_name,
                                played_at=meta_data['time_played_at'],
                                game_map=meta_data['game_map'],
                            )
                            replay.save()

                            file_contents = file.open(mode='rb')
                            current_replay = default_storage.open(bucket_path, 'w')
                            current_replay.write(file_contents.read())
                            current_replay.close()
                            uploaded = True
                            break

                    if uploaded is False:
                        bucket_path = f'{user.email}/{filename}'

                        player_battletags = []
                        for battletag in player_info.keys():
                            player_battletags.append(battletag)

                        replay = UnauthenticatedReplay(
                            file_hash=file_hash,
                            user_account=EmailAddress.objects.get(user=user),
                            player1_battletag=player_battletags[0],
                            player2_battletag=player_battletags[1],
                            played_at=meta_data['time_played_at'],
                            game_map=meta_data['game_map'],
                        )
                        replay.save()

                        file_contents = file.open(mode='rb')
                        current_replay = default_storage.open(bucket_path, 'w')
                        current_replay.write(file_contents.read())
                        current_replay.close()
                else:
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
