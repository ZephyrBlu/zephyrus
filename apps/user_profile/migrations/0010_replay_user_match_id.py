# Generated by Django 2.2.4 on 2019-09-19 06:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user_profile', '0009_auto_20190817_2050'),
    ]

    operations = [
        migrations.AddField(
            model_name='replay',
            name='user_match_id',
            field=models.IntegerField(max_length=1, null=True),
        ),
    ]
