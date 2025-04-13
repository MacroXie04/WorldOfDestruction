from django import forms
from index.models import CountryTemplate

class CountryFromTemplateForm(forms.Form):
    template = forms.ModelChoiceField(
        queryset=CountryTemplate.objects.all(),
        label="Choose a Country Template"
    )