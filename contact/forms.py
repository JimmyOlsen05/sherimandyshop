from django import forms

class ContactForm(forms.Form):
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'style': 'background: #0f172a; border: 1px solid #334155; color: #fff; padding: 12px; border-radius: 8px;'
        })
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'style': 'background: #0f172a; border: 1px solid #334155; color: #fff; padding: 12px; border-radius: 8px;'
        })
    )
    subject = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'style': 'background: #0f172a; border: 1px solid #334155; color: #fff; padding: 12px; border-radius: 8px;'
        })
    )
    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'style': 'background: #0f172a; border: 1px solid #334155; color: #fff; padding: 12px; border-radius: 8px; height: 150px;',
            'rows': 5
        })
    )
