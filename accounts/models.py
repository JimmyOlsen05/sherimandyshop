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

    # Required fields
    is_admin = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)  # Default to False for email verification
    is_superadmin = models.BooleanField(default=False)
    
    # Important: These fields are required by Django's authentication system
    date_joined = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(default=timezone.now)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    objects = AccountManger()

    def __str__(self):
        return self.email
    
    def full_name(self):
        return f'{self.first_name} {self.last_name}'

    def has_perm(self, perm, obj=None):
        return self.is_admin

    def has_module_perms(self, add_label):
        return True

    def send_verification_email(self, request):
        try:
            current_site = get_current_site(request)
            mail_subject = 'Activate Your SHERIMANDY SHOP Account'
            uid = urlsafe_base64_encode(force_bytes(self.pk))
            token = default_token_generator.make_token(self)
            
            message = render_to_string('shop/accounts/account_verification_email.html', {
                'user': self,
                'domain': current_site.domain,
                'uid': uid,
                'token': token,
                'protocol': 'https' if request.is_secure() else 'http'
            })
            
            email = EmailMessage(
                mail_subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [self.email],
            )
            email.content_subtype = 'html'
            email.send(fail_silently=False)
            
        except Exception as e:
            # Log the error for debugging
            print(f"Email sending failed: {str(e)}")
            raise e

class UserProfile(models.Model):
    user = models.OneToOneField(Account, on_delete=models.CASCADE)
    address = models.TextField(blank=True, max_length=500)
    city = models.CharField(blank=True, max_length=20)
    state = models.CharField(blank=True, max_length=20)
    country = models.CharField(blank=True, max_length=20)

    def __str__(self):
        return self.user.first_name
