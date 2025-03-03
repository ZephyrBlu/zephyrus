from django.db import models
from allauth.account.models import EmailAddress
from django.contrib.postgres.fields import JSONField


class FeatureVote(models.Model):
    vote_id = models.UUIDField(editable=False)
    user_account = models.ForeignKey(
        EmailAddress,
        to_field='email',
        on_delete=models.CASCADE
    )
    feature = models.CharField(max_length=100)
    comment = models.CharField(max_length=100)
    submitted_at = models.DateTimeField(auto_now_add=True)


class BattlenetAccount(models.Model):
    id = models.CharField(unique=True, null=False, max_length=100)
    battletag = models.CharField(primary_key=True, max_length=100)
    user_account = models.ForeignKey(
        EmailAddress,
        to_field='email',
        on_delete=models.CASCADE
    )
    region_profiles = JSONField()
    linked_at = models.DateTimeField(auto_now_add=True)


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


class Feedback(models.Model):
    ISSUE = 'I'
    SUGGESTION = 'S'
    FEEDBACK_TYPES = [
        (ISSUE, 'Issue'),
        (SUGGESTION, 'Suggestion'),
    ]
    feedback = models.CharField(max_length=300)
    feedback_type = models.CharField(
        max_length=1,
        choices=FEEDBACK_TYPES,
    )
    user_account = models.ForeignKey(
        EmailAddress,
        to_field='email',
        on_delete=models.CASCADE
    )
    submitted_at = models.DateTimeField(auto_now_add=True)
