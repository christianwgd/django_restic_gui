from django import forms


class RestoreForm(forms.Form):
    path = forms.CharField()