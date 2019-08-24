from .utils.mvp import main as parse_replay
from django.core.files.storage import default_storage
from apps.user_profile.models import Replay, BattlenetAccount
from allauth.account.models import EmailAddress
from django.core.exceptions import ObjectDoesNotExist


def process_file(replay_file, request, file_hash):
    user = request.user

    players, summary_stats, metadata = parse_replay(replay_file)

    if players is None:
        return

    player_summary = {}
    player_summary[1] = vars(players[1])
    player_summary[2] = vars(players[2])

    filename = replay_file.name

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
            try:
                player_battlenet_account = user_battlenet_accounts.get(**kwargs)
            except ObjectDoesNotExist:
                player_battlenet_account = None
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

        file_contents = replay_file.open(mode='rb')
        current_replay = default_storage.open(bucket_path, 'w')
        current_replay.write(file_contents.read())
        current_replay.close()
    else:
        pass
