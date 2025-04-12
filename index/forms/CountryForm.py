from django import forms
from index.models import Game, Country

class CountryForm(forms.ModelForm):
    class Meta:
        model = Country
        fields = ['name', 'money', 'population', 'population_growth_rate', 'land']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter country name'}),
            'money': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'initial money'}),
            'population': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'initial population'}),
            'population_growth_rate': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'initial population growth rate'}),
            'land': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'initial land'}),
        }