import os

from django import template
from django.utils.safestring import mark_safe

from repository.models import FileExt

register = template.Library()


generic = '<path fill-rule="evenodd" d="M4 0h8a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V2a2 2 0 0 1 2-2zm0 1a1 1 0 0 0-1 1v12a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1V2a1 1 0 0 0-1-1H4z"/>'

@register.simple_tag()
def get_file_icon(name):
    filename, file_extension = os.path.splitext(name)
    # remove the dot from extension
    file_extension = file_extension[1:]

    if file_extension is None or file_extension == '':
        return (mark_safe(generic))
    else:
        try:
            ext = FileExt.objects.get(name=file_extension.lower())
        except FileExt.DoesNotExist:
            return (mark_safe(generic))

    return mark_safe(ext.type.svg_path)
