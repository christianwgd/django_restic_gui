from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import gettext_lazy as _


class Repository(models.Model):

    class Meta:
        verbose_name = _('Repository')
        verbose_name_plural = _('Repositories')

    def __str__(self):
        return self.name

    name = models.CharField(max_length=100, verbose_name=_('Name'))
    password = models.CharField(max_length=100, verbose_name=_('Password'))
    path = models.FilePathField(
        allow_files=False, allow_folders=True,
        verbose_name=_('Path'), path=settings.LOCAL_BACKUP_PATH
    )


class CallStack(models.Model):

    class Meta:
        ordering = ['level']

    def __str__(self):
        return '{} {}'.format(self.level, self.name)

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
        return '{} {}'.format(self.timestamp, self.repo)

    user = models.ForeignKey(User, verbose_name=_('User'), on_delete=models.DO_NOTHING)
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name=_('Timestamp'))
    action = models.CharField(max_length=2, choices=ACTION_CHOICES, verbose_name=_('Action'))
    repo = models.ForeignKey(Repository, on_delete=models.DO_NOTHING, verbose_name=_('Repository'))
    data = models.CharField(max_length=200, verbose_name=_('Data'))
