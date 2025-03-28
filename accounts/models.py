from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.utils import timezone
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from mailjet_rest import Client
import json

class AccountManger(BaseUserManager):
    def create_user(self, first_name, last_name, username, email, password=None):
        if not email:
            raise ValueError('User must have an email address')
        if not username:
            raise ValueError('User must have an username')

        user = self.model(
            email=self.normalize_email(email),
            first_name=first_name,
            last_name=last_name,
            username=username,
            date_joined=timezone.now(),
            last_login=timezone.now(),
        )
        user.set_password(password)
        user.is_active = False  # User starts as inactive until email verification
        user.save(using=self._db)
        return user
    
    def create_superuser(self, first_name, last_name, username, email, password):
        user = self.create_user(
            email=self.normalize_email(email),
            first_name=first_name,
            last_name=last_name,
            username=username,
            password=password,
        )
        user.is_admin = True
        user.is_active = True
        user.is_staff = True
        user.is_superadmin = True
        user.save(using=self._db)
        return user

class Account(AbstractBaseUser):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    username = models.CharField(max_length=50, unique=True)
    email = models.EmailField(max_length=100, unique=True)
    phone_number = models.CharField(max_length=50)
    
    # required fields
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(auto_now_add=True)
    is_admin = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    is_superadmin = models.BooleanField(default=False)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
    
    objects = AccountManger()
    
    def send_verification_email(self, request):
        try:
            current_site = get_current_site(request)
            mail_subject = 'Activate your SHERIMANDY SHOP Account'
            context = {
                'user': self,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(self.pk)),
                'token': default_token_generator.make_token(self),
                'protocol': 'https' if request.is_secure() else 'http'
            }
            html_message = render_to_string('accounts/account_verification_email.html', context)
            
            # Print debug information
            print(f"Attempting to send verification email:")
            print(f"To: {self.email}")
            print(f"From: {settings.DEFAULT_FROM_EMAIL}")
            print(f"Subject: {mail_subject}")
            
            # Initialize Mailjet client
            mailjet = Client(auth=(settings.EMAILJET_API_KEY, settings.EMAILJET_SECRET_KEY), version='v3.1')
            
            # Prepare email data
            data = {
                'Messages': [
                    {
                        "From": {
                            "Email": "noreply@sherimandyshop.com",
                            "Name": "SHERIMANDY SHOP"
                        },
                        "To": [
                            {
                                "Email": self.email,
                                "Name": f"{self.first_name} {self.last_name}"
                            }
                        ],
                        "Subject": mail_subject,
                        "HTMLPart": html_message
                    }
                ]
            }
            
            # Send email using Mailjet API
            result = mailjet.send.create(data=data)
            
            if result.status_code == 200:
                print("Email sent successfully!")
                print(f"Mailjet Response: {json.dumps(result.json(), indent=2)}")
                return True
            else:
                print(f"Failed to send email. Status code: {result.status_code}")
                print(f"Mailjet Error: {json.dumps(result.json(), indent=2)}")
                raise Exception(f"Mailjet API error: {result.json()}")
                
        except Exception as e:
            print(f"Failed to send verification email:")
            print(f"Error type: {type(e).__name__}")
            print(f"Error message: {str(e)}")
            import traceback
            print(f"Traceback:\n{traceback.format_exc()}")
            raise e

    def __str__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        return self.is_admin

    def has_module_perms(self, add_label):
        return True

class UserProfile(models.Model):
    user = models.OneToOneField(Account, on_delete=models.CASCADE)
    address = models.TextField(blank=True, max_length=500)
    city = models.CharField(blank=True, max_length=20)
    state = models.CharField(blank=True, max_length=20)
    country = models.CharField(blank=True, max_length=20)

    def __str__(self):
        return self.user.first_name
