from django import forms
from index.models import Game, Country

class CreateGameForm(forms.ModelForm):
    class Meta:
        model = Game
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'please enter game name'}),
        }

