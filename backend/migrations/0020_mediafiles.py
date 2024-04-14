# Generated by Django 4.1.7 on 2024-04-14 00:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0019_conversation'),
    ]

    operations = [
        migrations.CreateModel(
            name='MediaFiles',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('conversation_sid', models.CharField(max_length=255)),
                ('s3url', models.CharField(blank=True, max_length=500, null=True)),
            ],
        ),
    ]
