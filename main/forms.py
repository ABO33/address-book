from django import forms
from .models import Contact
from .models import Tag

class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        fields = ['first_name', 'last_name', 'company_name', 'address', 'phone', 'email', 'comment', 'tags']
        widgets = {
            'tags': forms.CheckboxSelectMultiple(),
        }

class TagForm(forms.ModelForm):
    class Meta:
        model = Tag
        fields = ['name', 'color']
