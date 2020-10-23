from django import template
from django.urls import reverse

register = template.Library()


@register.simple_tag()
def geturl(name, repo_id, view, snapshot_id, path):
    return '{url}?id={id}&path={path}'.format(
        url=reverse(name, kwargs={'pk': repo_id, 'view': view}),
        repo_id=repo_id,
        id=snapshot_id,
        path=path
    )
