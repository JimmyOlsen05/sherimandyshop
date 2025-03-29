from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.utils import timezone
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage
from django.contrib.sites.shortcuts import get_current_site

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
            message = render_to_string('accounts/account_verification_email.html', context)
            
            # Print debug information
            print("="*50)
            print("Email Sending Debug Information:")
            print(f"To: {self.email}")
            print(f"From: {settings.DEFAULT_FROM_EMAIL}")
            print(f"Subject: {mail_subject}")
            print(f"SMTP Host: {settings.EMAIL_HOST}")
            print(f"SMTP Port: {settings.EMAIL_PORT}")
            print(f"SMTP User: {settings.EMAIL_HOST_USER}")
            print(f"Using TLS: {settings.EMAIL_USE_TLS}")
            print(f"Domain: {current_site.domain}")
            print("="*50)
            
            email = EmailMessage(
                subject=mail_subject,
                body=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[self.email],
            )
            email.content_subtype = "html"
            
            # Try to establish SMTP connection first
            from smtplib import SMTP
            try:
                with SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT) as server:
                    server.ehlo()
                    if settings.EMAIL_USE_TLS:
                        server.starttls()
                    server.ehlo()
                    server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
                    print("SMTP connection test successful!")
            except Exception as smtp_error:
                print(f"SMTP Connection Test Failed:")
                print(f"Error: {str(smtp_error)}")
                raise
            
            # If SMTP test passed, send the actual email
            email.send(fail_silently=False)
            print("Email sent successfully!")
            return True
            
        except Exception as e:
            print("="*50)
            print("Email Sending Failed:")
            print(f"Error Type: {type(e).__name__}")
            print(f"Error Message: {str(e)}")
            import traceback
            print(f"Full Traceback:\n{traceback.format_exc()}")
            print("="*50)
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
