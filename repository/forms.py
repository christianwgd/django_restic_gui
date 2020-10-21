from bootstrap_modal_forms.forms import BSModalForm
from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from repository.models import Repository


class RepositoryForm(forms.ModelForm):
    password2 = forms.CharField(
        max_length='100', label=_('Password confirm'),
        widget=forms.PasswordInput
    )

    class Meta:
        model = Repository
        fields = ['name', 'password', 'password2']
        widgets = {
            'password': forms.PasswordInput,
        }

    def clean(self):
        cleaned_data = super(RepositoryForm, self).clean()
        password = cleaned_data.get('password')
        password2 = cleaned_data.get('password2')
        if password and password2:
            if password != password2:
                raise ValidationError(
                    _('The two password fields didn’t match.'),
                    code='password_mismatch',
                )
        return cleaned_data


class RestoreForm(BSModalForm):
    path = forms.CharField(label=_('Restore to path'))


class NewBackupForm(BSModalForm):
    path = forms.CharField(label=_('Backup directory'))