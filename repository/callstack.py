from copy import deepcopy

from repository.models import CallStack


def push(name, path):
    count = CallStack.objects.count()
    CallStack.objects.create(level=count, name=name, path=path)


def pop():
    obj = CallStack.objects.all().order_by('-level').first()
    if obj:
        ret = deepcopy(obj)
        obj.delete()
        return ret
    return None


def peek():
    return CallStack.objects.all().order_by('-level').first()


def delete_to(name):
    try:
        obj = CallStack.objects.get(name=name)
        CallStack.objects.filter(level__gte=obj.level).delete()
    except CallStack.DoesNotExist:
        pass


def clear():
    CallStack.objects.all().delete()