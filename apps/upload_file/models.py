from django.db import models
from django.contrib.postgres.fields import JSONField

class Replay(models.Model):
    file = models.FileField(upload_to='replays/')
    uploaded_at = models.DateTimeField(auto_now_add=True)


class ReplayInfo(models.Model):
    # timeline = JSONField()
    player1 = JSONField()
    player2 = JSONField()
    uploaded_at = models.DateTimeField(auto_now_add=True)
