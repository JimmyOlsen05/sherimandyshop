from django import forms
from .models import Account, UserProfile
import re

class RegisterationFrom(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter password',
        'id': 'id_password'
    }))
    repeat_password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Confirm password',
        'id': 'id_repeat_password'
    }))
    
    class Meta:
        model = Account
        fields = ['first_name', 'last_name', 'phone_number', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter first name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter last name'
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter phone number',
                'type': 'tel'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter email'
            })
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        # Remove any trailing ">" characters
        email = email.rstrip('>')
        # Remove "www." prefix if present
        if email.startswith('www.'):
            email = email[4:]
        if Account.objects.filter(email=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if len(password) < 8:
            raise forms.ValidationError("Password must be at least 8 characters long")
        if not re.search("[A-Z]", password):
            raise forms.ValidationError("Password must contain at least one uppercase letter")
        if not re.search("[a-z]", password):
            raise forms.ValidationError("Password must contain at least one lowercase letter")
        if not re.search("[0-9]", password):
            raise forms.ValidationError("Password must contain at least one number")
        if not re.search("[!@#$%^&*(),.?\":{}|<>]", password):
            raise forms.ValidationError("Password must contain at least one special character")
        return password

    def clean(self):
        cleaned_data = super(RegisterationFrom, self).clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('repeat_password')

        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Passwords do not match")
            
        return cleaned_data

class UserForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ('first_name', 'last_name', 'phone_number', 'email')

    def __init__(self, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'

    def clean_email(self):
        email = self.cleaned_data.get('email')
        # Remove any trailing ">" characters
        email = email.rstrip('>')
        # Remove "www." prefix if present
        if email.startswith('www.'):
            email = email[4:]
        if Account.objects.filter(email=email).exclude(id=self.instance.id).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ('address', 'city', 'state', 'country')

    def __init__(self, *args, **kwargs):
        super(UserProfileForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'
