# Generated by Django 2.1.4 on 2019-05-04 03:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user_profile', '0002_auto_20190502_2150'),
    ]

    operations = [
        migrations.AddField(
            model_name='authenticatedreplay',
            name='opponent_profile_id',
            field=models.CharField(default=8369190, max_length=20),
            preserve_default=False,
        ),
    ]
