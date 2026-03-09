from django import forms
from .models import ImageStory


class ImageStoryForm(forms.ModelForm):
    """Form for uploading an image and selecting a language."""

    class Meta:
        model = ImageStory
        fields = ['image', 'language']
        widgets = {
            'image': forms.ClearableFileInput(attrs={
                'accept': 'image/*',
                'id': 'image-input',
            }),
            'language': forms.Select(attrs={
                'id': 'language-select',
            }),
        }
