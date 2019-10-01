from django.db import models
from apps.user_profile.models import Replay
from rest_framework import serializers


class ReplaySerializer(serializers.ModelSerializer):
    class Meta:
        model = Replay
        fields = [
            'file_hash',
            'players',
            'user_match_id',
            'match_data',
            'match_length',
            'battlenet_account',
            'map',
            'played_at',
            'region_id',
            'win'
        ]
