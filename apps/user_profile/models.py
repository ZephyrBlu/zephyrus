from django.db import models
from allauth.account.models import EmailAddress


class BattlenetAccount(models.Model):
    id = models.CharField(primary_key=True, max_length=100)
    career_games = models.PositiveIntegerField()
    profile_link = models.CharField(max_length=100)
    user_account = models.ForeignKey(EmailAddress, on_delete=models.CASCADE)
