from django import forms


class IngredientForm(forms.Form):
    ingredients = forms.CharField(widget=forms.Textarea(attrs={"rows": 3}), label="List ingredients you have")