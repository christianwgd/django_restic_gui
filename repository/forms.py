from bootstrap_modal_forms.forms import BSModalForm
from django import forms
from django.utils.translation import gettext_lazy as _


class RestoreForm(BSModalForm):
    path = forms.CharField(label=_('Restore to path'))