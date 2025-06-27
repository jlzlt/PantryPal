from django import forms
from .models import RecipeComment


class IngredientForm(forms.Form):
    ingredients = forms.CharField(widget=forms.HiddenInput(), required=False)

class RecipeCommentForm(forms.ModelForm):
    class Meta:
        model = RecipeComment
        fields = ['text', 'image']
        widgets = {
            'text': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Add a comment...',
                'maxlength': 1000,
            }),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }
        labels = {
            'text': '',
            'image': 'Attach photo (optional)',
        }
    
    def clean_text(self):
        text = self.cleaned_data.get('text', '')
        if len(text) > 1000:
            raise forms.ValidationError('Comments cannot exceed 1000 characters.')
        return text