import time
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
                self.log_stats_for_repo(repo)
            except Repository.DoesNotExist:
                raise CommandError(_('Repository does not exist: {}'.format(options['repo'])))
        else:
            repos = Repository.objects.all()
            for repo in repos:
                self.log_stats_for_repo(repo)

    def log_stats_for_repo(self, repo):
        t0 = time.time()
        self.stdout.write(
            self.style.SUCCESS(
                '%s "%s" ...' % (_('Logging stats for repository'), repo.name)
            )
        )
        try:
            LogRepoSize(repo)
            time.sleep(1)
            t1 = time.time()
            self.stdout.write(
                self.style.SUCCESS(
                    _('done in %.2f seconds') % (t1 - t0)
                )
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(
                    str(e)
                )
            )
