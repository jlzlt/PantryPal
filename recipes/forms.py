from django import forms


class IngredientForm(forms.Form):
    ingredients = forms.CharField(widget=forms.HiddenInput(), required=False)