from django.db import models
from allauth.account.models import EmailAddress
from django.contrib.postgres.fields import JSONField


class BattlenetAccount(models.Model):
    id = models.CharField(unique=True, null=False, max_length=100)
    battletag = models.CharField(primary_key=True, max_length=100)
    user_account = models.ForeignKey(
        EmailAddress,
        to_field='email',
        on_delete=models.CASCADE
    )
    region_profiles = JSONField()


class Replay(models.Model):
    file_hash = models.CharField(max_length=64)
    user_account = models.ForeignKey(
        EmailAddress,
        to_field='email',
        on_delete=models.CASCADE
    )
    battlenet_account = models.ForeignKey(
        BattlenetAccount,
        to_field='battletag',
        null=True,
        on_delete=models.CASCADE
    )
    players = JSONField()
    user_match_id = models.IntegerField(null=True)
    match_data = JSONField()
    match_length = models.IntegerField()
    played_at = models.DateTimeField()
    map = models.CharField(max_length=100)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    region_id = models.IntegerField()
    win = models.BooleanField(null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['file_hash', 'user_account'],
                name='unique_replay'
            )
        ]
