from django.conf import settings
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

