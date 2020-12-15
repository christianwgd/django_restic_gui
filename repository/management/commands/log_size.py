from django.core.management.base import BaseCommand, CommandError
from django.utils.translation import gettext_lazy as _

from repository.models import Repository
from repository.views import LogRepoSize


class Command(BaseCommand):
    help = _('Log size of repositories')

    def add_arguments(self, parser):
        parser.add_argument(
            '--repo',
            type=str,
            help=_('Repository, to log the size for, if not provided the size of all repositories is logged.')
        )

    def handle(self, *args, **options):
        if options['repo']:
            try:
                repo = Repository.objects.get(name=options['repo'])
            except Repository.DoesNotExist:
                raise CommandError(_('Repository does not exist: {}'.format(options['repo'])))
            LogRepoSize(repo)
            self.stdout.write(
                self.style.SUCCESS(
                    _('Successfully logged size for {}'.format(options['repo']))
                )
            )
        else:
            repos = Repository.objects.all()
            for repo in repos:
                LogRepoSize(repo)
            self.stdout.write(
                self.style.SUCCESS(
                    _('Successfully logged size for all repositories')
                )
            )
