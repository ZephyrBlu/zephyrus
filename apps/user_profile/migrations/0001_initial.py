# Generated by Django 2.1.4 on 2019-02-08 07:29

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('account', '0002_email_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='BattlenetAccount',
            fields=[
                ('id', models.CharField(max_length=100)),
                ('battletag', models.CharField(max_length=100, primary_key=True, serialize=False)),
                ('user_account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='account.EmailAddress')),
            ],
        ),
    ]
