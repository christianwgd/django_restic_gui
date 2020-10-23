import json
import os
import subprocess
from types import SimpleNamespace

from bootstrap_modal_forms.generic import BSModalFormView
from dateutil.parser import parse
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.text import slugify
from django.views.generic import ListView, DetailView, FormView, UpdateView, CreateView
from django.utils.translation import gettext_lazy as _

from repository.callstack import push, pop, delete_to, clear, peek
from repository.forms import RestoreForm, RepositoryForm, NewBackupForm
from repository.models import Repository, CallStack


class RepositoryList(LoginRequiredMixin, ListView):
    model = Repository

    def get(self, request, *args, **kwargs):
        clear()
        return super(RepositoryList, self).get(request, *args, **kwargs)


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

        result = subprocess.run(
            ['restic', 'init', '-r', path],
            stdout=subprocess.PIPE,
            env=my_env
        )

        form.instance.path = path
        return super(RepositoryCreate, self).form_valid(form)
        


class RepositorySnapshots(LoginRequiredMixin, DetailView):
    model = Repository
    template_name = 'repository/repository_snapshots.html'

    def get_context_data(self, **kwargs):
        clear()
        ctx = super(RepositorySnapshots, self).get_context_data(**kwargs)
        repo = self.get_object()

        my_env = os.environ.copy()
        my_env["RESTIC_PASSWORD"] = repo.password

        result = subprocess.run(
            ['restic', '-r', repo.path, 'snapshots', '--json'],
            stdout=subprocess.PIPE,
            env=my_env
        )
        snapshots = json.loads(result.stdout, object_hook=lambda d: SimpleNamespace(**d))
        if snapshots is not None:
            for snap in snapshots:
                snap.timestamp = parse(snap.time)
            ctx['snapshots'] = reversed(snapshots)
        else:
            ctx['snapshots'] = None
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
        my_env = os.environ.copy()
        my_env["RESTIC_PASSWORD"] = repo.password

        result = subprocess.run(
            ['restic', '-r', repo.path, 'ls', short_id, path, '--json'],
            stdout=subprocess.PIPE,
            env=my_env
        )

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
            my_env = os.environ.copy()
            my_env["RESTIC_PASSWORD"] = repo.password

            if dest_path == '':
                result = subprocess.run(
                    [
                        'restic', '-r', repo.path, 'restore', snapshot_id,
                        '--include', source_path, '--target', '/'
                    ],
                    stdout=subprocess.PIPE,
                    env=my_env
                )
                msg = _('{src} successfully restored').format(
                    src=source_path,
                    dest=dest_path
                )
            else:
                result = subprocess.run(
                    [
                        'restic', '-r', repo.path, 'restore', snapshot_id,
                        '--include', source_path, '--target', dest_path
                    ],
                    stdout=subprocess.PIPE,
                    env=my_env
                )
                msg = _('{src} successfully restored to {dest}').format(
                    src=source_path,
                    dest=dest_path
                )
            messages.success(self.request, msg)
        return redirect(self.get_success_url())


class BackupView(LoginRequiredMixin, DetailView):
    model = Repository

    def get_success_url(self):
        return reverse(
            'repository:snapshots',
            kwargs={
                'pk': self.request.session['repo_id'],
            }
        )

    def get(self, request, *args, **kwargs):
        short_id = self.request.GET.get('id', None)
        path = self.request.GET.get('path', None)
        self.request.session['path'] = path
        self.request.session['short_id'] = short_id

        # backup path
        repo = self.get_object()
        my_env = os.environ.copy()
        my_env["RESTIC_PASSWORD"] = repo.password
        result = subprocess.run(
            ['restic', '-r', repo.path, 'backup', path],
            stdout=subprocess.PIPE,
            env=my_env
        )
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
            my_env = os.environ.copy()
            my_env["RESTIC_PASSWORD"] = repo.password
            result = subprocess.run(
                ['restic', '-r', repo.path, 'backup', path],
                stdout=subprocess.PIPE,
                env=my_env
            )
            messages.success(self.request,
                _('Backup of {path} successfully completed'.format(
                    path=path,
                )),
            )
        return redirect(self.get_success_url())

