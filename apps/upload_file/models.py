from django.db import models
from django.contrib.postgres.fields import JSONField
from apps.user_profile.models import BattlenetAccount


class ReplayInfo(models.Model):
    bucket_path = models.CharField(max_length=200)
    battlenet_account = models.ForeignKey(BattlenetAccount, on_delete=models.CASCADE)
    # timeline = JSONField()
    player1 = JSONField()
    player2 = JSONField()
    uploaded_at = models.DateTimeField(auto_now_add=True)
