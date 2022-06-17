import json
import os
import shutil
import subprocess
from types import SimpleNamespace

import humanize
from bootstrap_modal_forms.generic import BSModalFormView
from dateutil.parser import parse
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.http import FileResponse, JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.formats import date_format
from django.utils.text import slugify
from django.views.generic import ListView, DetailView, UpdateView, CreateView
from django.utils.translation import gettext_lazy as _

from repository.callstack import push, delete_to, clear, peek
from repository.forms import RestoreForm, RepositoryForm, NewBackupForm
from repository.models import Repository, CallStack, Journal, RepoSize


def restic_command(repo, command):
    my_env = os.environ.copy()
    my_env["RESTIC_PASSWORD"] = repo.password
    for key, value in repo.extra_keys.items():
        my_env[key] = value

    if settings.DEBUG:
        print('Issue restic_command: "%s"' % command)
    #return subprocess.run(command, stdout=subprocess.PIPE, env=my_env, capture_output=True)

    # Capture stderr so we can later display usefull messages in case of error
    # capture_output=True requires Python 3.7 or higher
    return subprocess.run(command, env=my_env, capture_output=True)


def get_directory_size(directory):
    """Returns the `directory` size in bytes."""
    total = 0
    try:
        for entry in os.scandir(directory):
            if entry.is_file():
                # if it's a file, use stat() function
                total += entry.stat().st_size
            elif entry.is_dir():
                # if it's a directory, recursively call this function
                total += get_directory_size(entry.path)
    except NotADirectoryError:
        # if `directory` isn't a directory, get the file size then
        return os.path.getsize(directory)
    except (PermissionError, FileNotFoundError):
        # if for whatever reason we can't open the folder, return 0
        return 0
    return total


def LogRepoSize(repo):
    RepoSize.objects.create(repo=repo, size=get_directory_size(repo.path))


class RepositoryList(LoginRequiredMixin, ListView):
    model = Repository

    def get(self, request, *args, **kwargs):
        clear()
        return super(RepositoryList, self).get(request, *args, **kwargs)

    def get_queryset(self):
        qs = Repository.objects.all()
        for repo in qs:
            repo.size = humanize.naturalsize(get_directory_size(repo.path), binary=False)
        return qs

    def get_context_data(self, *, object_list=None, **kwargs):
        ctx = super(RepositoryList, self).get_context_data(**kwargs)
        try:
            total, used, free = shutil.disk_usage(settings.LOCAL_BACKUP_PATH)
            ratio = int(used / total * 100)
        except FileNotFoundError as e:
            total, used, free = 0, 0, 0
            ratio = 0
        ctx['total'] = humanize.naturalsize(total, binary=False)
        ctx['used'] = humanize.naturalsize(used, binary=False)
        ctx['free'] = humanize.naturalsize(free, binary=False)
        ctx['ratio'] = ratio
        ctx['freeratio'] = 100 - ratio
        if ratio < 50:
            ctx['bar_class'] = 'bg-success'
        elif ratio < 80:
            ctx['bar_class'] = 'bg-warning'
        else:
            ctx['bar_class'] = 'bg-danger'
        return ctx


class RepositoryChart(LoginRequiredMixin, DetailView):
    model = Repository
    template_name = 'repository/repository_chart.html'


def repository_chart(request, repo_id=None):
    labels = []
    data = []
    data_list = RepoSize.objects.filter(repo__pk=repo_id)
    unit = 'GB'
    for item in data_list:
        labels.append(date_format(item.timestamp, "SHORT_DATE_FORMAT"))
        data.append(item.size/float(1 << 30))
    return JsonResponse(data={'labels': labels, 'data': data, 'unit': unit})


class RepositoryUpdate(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Repository
    form_class = RepositoryForm
    success_message = _('Repository changed.')

    def get_success_url(self):
        return reverse('repository:list')


class RepositoryCreate(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = Repository
    form_class = RepositoryForm
    success_message = _('Repository created')

    def get_success_url(self):
        return reverse('repository:list')

    def form_valid(self, form):
        path = os.path.join(
            settings.LOCAL_BACKUP_PATH,
            slugify(form.cleaned_data['name'])
        )

        my_env = os.environ.copy()
        my_env["RESTIC_PASSWORD"] = form.cleaned_data['password']
        sudo = 'sudo' in form.cleaned_data

        command = ['restic', 'init', '-r', path]
        if sudo:
            command.insert(0, 'sudo')

        result = subprocess.run(command, stdout=subprocess.PIPE, env=my_env)

        form.instance.path = path
        return super(RepositoryCreate, self).form_valid(form)



class RepositorySnapshots(LoginRequiredMixin, DetailView):
    model = Repository
    template_name = 'repository/repository_snapshots.html'

    def get_context_data(self, **kwargs):
        clear()
        ctx = super(RepositorySnapshots, self).get_context_data(**kwargs)
        repo = self.get_object()

        command = ['restic', '-r', repo.path, 'snapshots', '--json']
        result = restic_command(repo, command)
        ctx['snapshots'] = None
        try:
            snapshots = json.loads(result.stdout, object_hook=lambda d: SimpleNamespace(**d))
            if snapshots is not None:
                for snap in snapshots:
                    snap.timestamp = parse(snap.time)
                ctx['snapshots'] = reversed(snapshots)
        except json.JSONDecodeError:
            # Hopefully, something usefull can be retrieved from stdout
            messages.error(self.request, result.stderr.decode())
        return ctx


class FileBrowse(LoginRequiredMixin, DetailView):
    model = Repository

    def get(self, request, *args, **kwargs):
        request.session['view'] = kwargs.get('view', 'icon')
        return super(FileBrowse, self).get(request, *args, **kwargs)

    def get_template_names(self):
        return ['repository/file_browse_{}.html'.format(self.request.session['view'])]

    def get_context_data(self, **kwargs):
        short_id = self.request.GET.get('id', None)
        path = self.request.GET.get('path', None)

        ctx = super(FileBrowse, self).get_context_data(**kwargs)
        repo = self.get_object()

        command = ['restic', '-r', repo.path, 'ls', short_id, path, '--json']
        result = restic_command(repo, command)

        results = result.stdout.decode(encoding='UTF-8').split('\n')
        pathlist = []
        for item in results:
            try:
                if item != '':
                    json_item = json.loads(item, object_hook=lambda d: SimpleNamespace(**d))
                    if json_item.struct_type == 'snapshot':
                        snapshot = json_item
                    elif json_item.struct_type == 'node':
                        if path == json_item.path:
                            delete_to(json_item.name)
                            push(json_item.name, json_item.path)
                        else:
                            pathlist.append(json_item)
                    else:
                        pass
            except:
                # import traceback
                # traceback.print_exc()
                pass

        ctx['snapshot'] = snapshot
        ctx['path_list'] = pathlist
        ctx['current'] = peek()
        ctx['stack'] = CallStack.objects.all()
        return ctx


class RestoreView(LoginRequiredMixin, BSModalFormView):
    form_class = RestoreForm
    template_name = 'repository/restore_modal.html'
    success_url = '/'

    def get(self, request, *args, **kwargs):
        request.session['view'] = kwargs.get('view', 'icon')
        request.session['repo_id'] = kwargs.get('pk', None)
        request.session['snapshot_id'] = request.GET.get('id', None)
        request.session['source_path'] = request.GET.get('path', None)
        request.session['return'] = request.GET.get('return', None)
        return super(RestoreView, self).get(request, *args, **kwargs)

    def get_success_url(self):
        if self.request.session['return']:
            return reverse(
                'repository:snapshots',
                kwargs={'pk': self.request.session['repo_id']}
            )
        else:
            rev_url = reverse(
                'repository:browse',
                kwargs={
                    'pk': self.request.session['repo_id'],
                    'view': self.request.session['view']
                }
            )
            source_path = self.request.session['source_path']
            parts = source_path.split('/')
            url = '{url}?id={id}&path={path}'.format(
                url=rev_url,
                id=self.request.session['snapshot_id'],
                path='/'.join(parts[:-1])
            )
            return url

    def form_valid(self, form):
        if not self.request.is_ajax():
            snapshot_id = self.request.session['snapshot_id']
            source_path = self.request.session['source_path']
            dest_path = form.cleaned_data['path']

            # restore to path
            repo = Repository.objects.get(pk=self.request.session['repo_id'])

            if dest_path == '':
                command = [
                    'restic', '-r', repo.path, 'restore', snapshot_id,
                    '--include', source_path, '--target', '/'
                ]
                msg = _('{src} successfully restored').format(
                    src=source_path,
                    dest=dest_path
                )
                Journal.objects.create(
                    user=self.request.user,
                    repo=repo,
                    action='3',
                    data=source_path
                )
            else:
                command = [
                    'restic', '-r', repo.path, 'restore', snapshot_id,
                    '--include', source_path, '--target', dest_path
                ]
                msg = _('{src} successfully restored to {dest}').format(
                    src=source_path,
                    dest=dest_path
                )
                Journal.objects.create(
                    user=self.request.user,
                    repo=repo,
                    action='3',
                    data='{} --> {}'.format(source_path, dest_path)
                )
            result = restic_command(repo, command)
            messages.success(self.request, msg)
        return redirect(self.get_success_url())


class BackupView(LoginRequiredMixin, DetailView):
    model = Repository

    def get_success_url(self):
        return reverse(
            'repository:snapshots',
            kwargs={
                'pk': self.get_object().id,
            }
        )

    def get(self, request, *args, **kwargs):
        short_id = self.request.GET.get('id', None)
        path = self.request.GET.get('path', None)
        self.request.session['path'] = path
        self.request.session['short_id'] = short_id

        # backup path
        repo = self.get_object()
        command = ['restic', '-r', repo.path, 'backup', path]
        result = restic_command(repo, command)
        Journal.objects.create(
            user=self.request.user,
            repo=repo,
            action='1',
            data=path
        )
        LogRepoSize(repo)
        messages.success(self.request,
            _('Backup of {path} successfully completed'.format(
                 path=path,
            )),
        )
        return redirect(self.get_success_url())


class NewBackupView(LoginRequiredMixin, BSModalFormView):
    form_class = NewBackupForm
    template_name = 'repository/new_backup_modal.html'
    success_url = '/'

    def get(self, request, *args, **kwargs):
        request.session['repo_id'] = kwargs.get('pk', None)
        return super(NewBackupView, self).get(request, *args, **kwargs)

    def form_valid(self, form):
        if not self.request.is_ajax():
            path = form.cleaned_data['path']

            # backup path
            repo = Repository.objects.get(pk=self.request.session['repo_id'])
            command = ['restic', '-r', repo.path, 'backup', path]
            result = restic_command(repo, command)
            Journal.objects.create(
                user=self.request.user,
                repo=repo,
                action='1',
                data='{} --> {}'.format(path)
            )
            messages.success(self.request,
                _('Backup of {path} successfully completed'.format(
                    path=path,
                )),
            )
        return redirect(self.get_success_url())


class JournalView(LoginRequiredMixin, ListView):
    model = Journal


class Download(DetailView):
    model = Repository

    def get_success_url(self):
        if self.request.session['return']:
            return reverse(
                'repository:snapshots',
                kwargs={'pk': self.request.session['repo_id']}
            )
        else:
            rev_url = reverse(
                'repository:browse',
                kwargs={
                    'pk': self.request.session['repo_id'],
                    'view': self.request.session['view']
                }
            )
            source_path = self.request.session['source_path']
            parts = source_path.split('/')
            url = '{url}?id={id}&path={path}'.format(
                url=rev_url,
                id=self.request.session['snapshot_id'],
                path='/'.join(parts[:-1])
            )
            return url

    def get(self, request, *args, **kwargs):
        request.session['view'] = kwargs.get('view', 'icon')
        repo_id = kwargs.get('pk', None)
        snapshot_id = request.GET.get('id', None)
        path = request.GET.get('path', None)
        repo = Repository.objects.get(pk=repo_id)

        temp_path = getattr(settings, "TEMP_PATH", None)
        if temp_path is None:
            messages.error(
                self.request,
                _('You need to set the download path in localsetting.py to enable downloads')
            )
            return redirect(self.get_success_url())
        download_path = os.path.join(temp_path, slugify(repo.name))

        # restore to temp path
        command = [
            'restic', '-r', repo.path, 'restore', snapshot_id,
            '--include', path, '--target', download_path
        ]
        result = restic_command(repo, command)
        Journal.objects.create(
            user=self.request.user,
            repo=repo,
            action='2',
            data='{}'.format(path)
        )

        zip_filename = '{}_{}'.format(
            slugify(repo.name),
            os.path.basename(os.path.normpath(path))
        )
        zip_fullpath = os.path.join(temp_path, zip_filename)
        zip_dir = os.path.dirname((os.path.join(download_path, path[1:])))
        shutil.make_archive(
            zip_fullpath,
            'zip',
            zip_dir
        )

        zip_name = zip_filename + '.zip'
        zip_fullpath = os.path.join(temp_path, zip_name)

        zip_file = open(zip_fullpath, 'rb')
        resp = FileResponse(zip_file, content_type="application/force-download")
        resp['Content-Disposition'] = 'attachment; filename=%s' % zip_name

        os.remove(zip_fullpath)
        shutil.rmtree(download_path)
        return resp

