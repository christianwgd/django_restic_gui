import json
import os
import subprocess
from types import SimpleNamespace

from dateutil.parser import parse
from django.views.generic import ListView, DetailView

from repository.callstack import push, pop, delete_to, clear, peek
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