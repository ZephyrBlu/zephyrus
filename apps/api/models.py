from django.db import models
from apps.upload_file.models import ReplayInfo
from rest_framework import serializers

class ReplaySerializer(serializers.ModelSerializer):
    class Meta:
        model = ReplayInfo
        fields = ('player1', 'player2')
