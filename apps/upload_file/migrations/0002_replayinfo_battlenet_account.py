# Generated by Django 2.1.4 on 2019-04-26 00:03

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('user_profile', '0001_initial'),
        ('upload_file', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='replayinfo',
            name='battlenet_account',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='user_profile.BattlenetAccount'),
        ),
    ]
