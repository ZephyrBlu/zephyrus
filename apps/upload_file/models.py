from django.db import models
from django.contrib.postgres.fields import JSONField
from apps.user_profile.models import BattlenetAccount


class ReplayInfo(models.Model):
    file_hash = models.CharField(primary_key=True, max_length=200)
    battlenet_account = models.ForeignKey(BattlenetAccount, on_delete=models.CASCADE)
    # timeline = JSONField()
    user = JSONField()
    opponent = JSONField()
    played_at = models.DateTimeField()
    game_map = models.CharField(max_length=100)
    uploaded_at = models.DateTimeField(auto_now_add=True)
