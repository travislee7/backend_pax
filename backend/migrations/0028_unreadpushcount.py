# Generated by Django 4.1.7 on 2024-05-07 06:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0027_reviews_delete_review'),
    ]

    operations = [
        migrations.CreateModel(
            name='UnreadPushCount',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('player_id', models.CharField(max_length=255)),
                ('unreadPushFromPlayer', models.IntegerField(default=0)),
                ('coach_id', models.CharField(max_length=255)),
                ('unreadPushFromCoach', models.IntegerField(default=0)),
                ('category', models.CharField(max_length=100)),
            ],
        ),
    ]
