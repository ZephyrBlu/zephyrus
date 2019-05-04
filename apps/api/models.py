from django.db import models
from apps.user_profile.models import AuthenticatedReplay
from rest_framework import serializers


class ReplaySerializer(serializers.ModelSerializer):
    class Meta:
        model = AuthenticatedReplay
        fields = (
            'user_in_game_name',
            'opponent_in_game_name',
            'match_summary',
            'battlenet_account',
            'opponent_profile_id',
            'map',
            'played_at',
            'region_id'
        )
