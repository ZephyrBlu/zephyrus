# Generated by Django 2.1.4 on 2019-05-01 01:56

import django.contrib.postgres.fields.jsonb
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('user_profile', '0006_auto_20190427_1357'),
    ]

    operations = [
        migrations.RenameField(
            model_name='unauthenticatedreplay',
            old_name='player1_battlenet_id',
            new_name='player1_profile_id',
        ),
        migrations.RenameField(
            model_name='unauthenticatedreplay',
            old_name='player2_battlenet_id',
            new_name='player2_profile_id',
        ),
        migrations.AddField(
            model_name='battlenetaccount',
            name='profiles',
            field=django.contrib.postgres.fields.jsonb.JSONField(default=1),
            preserve_default=False,
        ),
    ]
