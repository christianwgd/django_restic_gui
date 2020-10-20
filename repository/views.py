import json
import os
import subprocess
from types import SimpleNamespace

from dateutil.parser import parse
from django.contrib import messages
from django.shortcuts import redirect
from django.views.generic import ListView, DetailView, FormView
from django.utils.translation import gettext_lazy as _

from repository.callstack import push, pop, delete_to, clear, peek
from repository.forms import RestoreForm
from repository.models import Repository, CallStack


class RepositoryList(ListView):
    model = Repository

    def get(self, request, *args, **kwargs):
        clear()
        return super(RepositoryList, self).get(request, *args, **kwargs)


class RepositorySnapshots(DetailView):
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
        for snap in snapshots:
            snap.timestamp = parse(snap.time)
        ctx['snapshots'] = reversed(snapshots)
        return ctx


class FileBrowse(DetailView):
    model = Repository
    template_name = 'repository/file_browse.html'

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
                import traceback
                traceback.print_exc()

        ctx['snapshot'] = snapshot
        ctx['path_list'] = pathlist
        ctx['current'] = peek()
        ctx['stack'] = CallStack.objects.all()
        return ctx


class RestoreView(FormView):
    form_class = RestoreForm
    template_name = 'repository/restore.html'
    success_url = '/'

    def get(self, request, *args, **kwargs):
        request.session['referer'] = request.META.get('HTTP_REFERER')
        request.session['repo_id'] = kwargs.get('pk', None)
        request.session['snapshot_id'] = request.GET.get('id', None)
        request.session['source_path'] = request.GET.get('path', None)
        return super(RestoreView, self).get(request, *args, **kwargs)

    def get_initial(self):
        initial = super().get_initial()
        source_path = self.request.session['source_path']
        if os.path.isfile(source_path):
            source_path = os.path.dirname(source_path)
        initial['path'] = source_path
        return initial

    def get_success_url(self):
        return self.request.session['referer']

    def form_valid(self, form):

        if 'cancel' in self.request.POST:
            return redirect(self.get_success_url())

        snapshot_id = self.request.session['snapshot_id']
        source_path = self.request.session['source_path']
        dest_path = form.cleaned_data['path']

        # restore to path
        repo = Repository.objects.get(pk=self.request.session['repo_id'])
        my_env = os.environ.copy()
        my_env["RESTIC_PASSWORD"] = repo.password

        result = subprocess.run(
            [
                'restic', '-r', repo.path, 'restore', snapshot_id,
                '--include', source_path, '--target', dest_path
            ],
            stdout=subprocess.PIPE,
            env=my_env
        )

        messages.success(self.request,
            _('{src} successfully restored to {dest}.'.format(
                src=source_path,
                dest=dest_path
            )),
        )
        return super(RestoreView, self).form_valid(form)


class BackupView(DetailView):
    model = Repository

    def get_success_url(self):
        return self.request.session['referer']

    def get(self, request, *args, **kwargs):
        short_id = self.request.GET.get('id', None)
        path = self.request.GET.get('path', None)
        print(short_id, path)

        # backup path
        #restic -r ~/backup/test2 backup ~/backup-test
        repo = self.get_object()
        print(repo)
        my_env = os.environ.copy()
        my_env["RESTIC_PASSWORD"] = repo.password
        result = subprocess.run(
            ['restic', '-r', repo.path, 'backup', path],
            stdout=subprocess.PIPE,
            env=my_env
        )
        messages.success(self.request,
            _('Backup of {path} successfully completed.'.format(
                 path=path,
            )),
        )
        return redirect(self.get_success_url())

