from django import forms

from .models import Inquiry


class InquiryForm(forms.ModelForm):
    """Customer-facing 'ask about this piece' form on the item detail page."""

    class Meta:
        model = Inquiry
        fields = ['name', 'email', 'message']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Your name'}),
            'email': forms.EmailInput(attrs={'placeholder': 'you@example.com'}),
            'message': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Your question about this piece…',
            }),
        }
        labels = {
            'name': 'Your name',
            'email': 'Your email',
            'message': 'Message',
        }
