from django.db import models
from allauth.account.models import EmailAddress
from django.contrib.postgres.fields import JSONField


class BattlenetAccount(models.Model):
    id = models.CharField(unique=True, null=False, max_length=100)
    battletag = models.CharField(primary_key=True, max_length=100)
    user_account = models.ForeignKey(EmailAddress, to_field='email', on_delete=models.CASCADE)
    region_profiles = JSONField()


# for replays associated with an authenticated battlenet account
class AuthenticatedReplay(models.Model):
    file_hash = models.CharField(max_length=200)
    battlenet_account = models.ForeignKey(BattlenetAccount, on_delete=models.CASCADE)
    # timeline = JSONField()
    match_summary = JSONField()
    user_in_game_name = models.CharField(max_length=50)
    opponent_in_game_name = models.CharField(max_length=50)
    played_at = models.DateTimeField()
    map = models.CharField(max_length=100)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    region_id = models.IntegerField()


# for replays uploaded to an account that are not linked
# to any of the authenticated battlenet accounts
# authenticated and unauthenticated replays are mutually exclusive
class UnauthenticatedReplay(models.Model):
    file_hash = models.CharField(max_length=200)
    user_account = models.ForeignKey(EmailAddress, to_field='email', on_delete=models.CASCADE)
    # timeline = JSONField()
    match_summary = JSONField()
    player1_profile_id = models.CharField(max_length=20)
    player2_profile_id = models.CharField(max_length=20)
    played_at = models.DateTimeField()
    map = models.CharField(max_length=100)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    region_id = models.IntegerField()
