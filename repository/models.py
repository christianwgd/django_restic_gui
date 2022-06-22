from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import gettext_lazy as _
from encrypted_model_fields.fields import EncryptedCharField


class Repository(models.Model):

    class Meta:
        verbose_name = _('Repository')
        verbose_name_plural = _('Repositories')

    def __str__(self):
        return self.name

    name = models.CharField(max_length=100, verbose_name=_('Name'))
    password = EncryptedCharField(max_length=100, verbose_name=_('Password'))
    # Treat path as a generic CharField, so we can accept either local paths or connection strings
    path = models.CharField(
        max_length=256, null=False, blank=True,
        help_text=_(
            'Enter either a local path or the connection string for '
            'remote backup repo, i.e.: "sftp:remote_backup:restic"'
        )
    )
    extra_keys = models.JSONField(null=False, blank=True, default=dict,
        help_text=_(
            "List KEY=VALUE pairs to be added to the env when connecting with this repo;"
            " place each key/value pair on it's own line"
        )
    )


class CallStack(models.Model):

    class Meta:
        ordering = ['level']

    def __str__(self):
        return f'{self.level} {self.name}'

    level = models.PositiveIntegerField(default=0, unique=True)
    name = models.CharField(max_length=100)
    path = models.CharField(max_length=200)


class FileType(models.Model):

    class Meta:
        verbose_name = _('File type')
        verbose_name_plural = _('File types')

    def __str__(self):
        return self.name

    name = models.CharField(max_length=50, verbose_name=_('Name'))
    svg_path = models.CharField(max_length=500, verbose_name=_('SVG Path'))


class FileExt(models.Model):

    class Meta:
        verbose_name = _('File extension')
        verbose_name_plural = _('File extensions')

    def __str__(self):
        return self.name

    name = models.CharField(max_length=50, unique=True, verbose_name=_('Name'))
    type = models.ForeignKey(
        FileType, on_delete=models.SET_NULL,
        null=True, blank=True, verbose_name=_('Type')
    )


ACTION_CHOICES = (
    ('1', _('Backup')),
    ('2', _('Download')),
    ('3', _('Restore')),
    ('4', _('New Repository')),
    ('5', _('Repository changed')),
)


class Journal(models.Model):

    class Meta:
        verbose_name = _('Journal')
        ordering = ['-timestamp']

    def __str__(self):
        return f'{self.timestamp} {self.repo}'

    user = models.ForeignKey(User, verbose_name=_('User'), on_delete=models.DO_NOTHING)
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name=_('Timestamp'))
    action = models.CharField(max_length=2, choices=ACTION_CHOICES, verbose_name=_('Action'))
    repo = models.ForeignKey(Repository, on_delete=models.DO_NOTHING, verbose_name=_('Repository'))
    data = models.CharField(max_length=200, verbose_name=_('Data'))


class RepoSize(models.Model):

    class Meta:
        verbose_name = _('Repository Size')
        verbose_name_plural = _('Repository Sizes')
        ordering = ['timestamp']

    def __str__(self):
        return f'{self.timestamp} {self.repo}'

    timestamp = models.DateTimeField(auto_now_add=True, verbose_name=_('Timestamp'))
    size = models.PositiveBigIntegerField(verbose_name=_('Size'))
    file_count = models.PositiveBigIntegerField(verbose_name=_('File count'))
    repo = models.ForeignKey(Repository, on_delete=models.CASCADE, verbose_name=_('Repository'))
