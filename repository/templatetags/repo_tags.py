from django import template
from django.urls import reverse
from django.conf import settings

register = template.Library()


@register.simple_tag()
def geturl(name, repo_id, view, snapshot_id, path):
    return '{url}?id={id}&path={path}'.format(
        url=reverse(name, kwargs={'pk': repo_id, 'view': view}),
        repo_id=repo_id,
        id=snapshot_id,
        path=path
    )


# settings value
@register.simple_tag
def settings_value(name):
    """
    usage:
        {% settings_value "LANGUAGE_CODE" %}
    or:
        {% settings_value 'ENABLE_FEATURE_A' as ENABLE_FEATURE_A %}
        {% if ENABLE_FEATURE_A %}
            ...
        {% endif %}
    """
    return getattr(settings, name, "")
