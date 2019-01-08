from django.db import models

class Replay(models.Model):
    file = models.FileField(upload_to='replays/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
