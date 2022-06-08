# Generated by Django 4.0.4 on 2022-06-08 10:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('repository', '0014_alter_reposize_options'),
    ]

    operations = [
        migrations.AlterField(
            model_name='repository',
            name='path',
            field=models.CharField(blank=True, help_text='Enter either a local path or the connection string for a remote backup repo, i.e.: "sftp:remote_backup:restic"', max_length=256),
        ),
    ]
