from django import forms
from django.utils.translation import gettext_lazy as _


class RestoreForm(forms.Form):
    path = forms.CharField(label=_('Path'))