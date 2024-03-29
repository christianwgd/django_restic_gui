# Generated by Django 4.0.5 on 2022-06-17 15:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('repository', '0016_alter_repository_password_alter_repository_path'),
    ]

    operations = [
        migrations.AddField(
            model_name='repository',
            name='extra_keys',
            field=models.JSONField(blank=True, default=dict, help_text="List KEY=VALUE pairs to be added to the env when connecting with this repo; place each key/value pair on it's own line"),
        ),
    ]
