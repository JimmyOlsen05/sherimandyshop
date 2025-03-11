from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages, auth
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.core.exceptions import ObjectDoesNotExist

# Verification email
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail

from .forms import RegisterationFrom, UserForm, UserProfileForm
from .models import Account, UserProfile
from cart.views import _cart_id
from cart.models import Cart, CartItem
from orders.models import Order, OrderProduct
import uuid
from oauth2_provider.models import Application
from oauth2_provider.views.generic import ProtectedResourceView
from oauth2_provider.decorators import protected_resource
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.urls import reverse
from django.conf import settings
import requests

@ensure_csrf_cookie
def register(request):
    if request.method == "POST":
        form = RegisterationFrom(request.POST)
        if form.is_valid():
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            phone_number = form.cleaned_data['phone_number']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            username = email.split("@")[0]
            
            try:
                user = Account.objects.create_user(
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    username=username,
                    password=password
                )
                user.phone_number = phone_number
                user.save()

                # Create a user profile
                profile = UserProfile()
                profile.user_id = user.id
                profile.save()

                # Send verification email
                user.send_verification_email(request)

                messages.success(request, 'Registration successful! Please check your email to activate your account.')
                return redirect(f"{reverse('accounts:register')}?command=verification")
                
            except Exception as e:
                messages.error(request, f'Failed to create account: {str(e)}')
                return redirect('accounts:register')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = RegisterationFrom()

    context = {
        'forms': form,
    }
    return render(request, 'shop/accounts/register.html', context)

def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = Account.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, Account.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, 'Your account has been activated successfully! You can now login.')
        return redirect('accounts:login')
    else:
        messages.error(request, 'Invalid activation link')
        return redirect('accounts:register')

@ensure_csrf_cookie
def login(request):
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')

    if request.method == "POST":
        email = request.POST['email']
        password = request.POST['password']

        user = auth.authenticate(email=email, password=password)

        if user is not None:
            if not user.is_active:
                messages.error(request, 'Please verify your email address before logging in.')
                return redirect('accounts:login')

            auth.login(request, user)
            
            # Get the next URL, but prevent redirect loops
            next_url = request.GET.get('next', '')
            if next_url and not next_url.startswith('/accounts/login'):
                return redirect(next_url)
            return redirect('accounts:dashboard')
        else:
            messages.error(request, 'Invalid login credentials')
            return redirect('accounts:login')

    return render(request, 'shop/accounts/login.html')


@login_required(login_url = 'accounts:login')
def logout(request):
    auth.logout(request)
    messages.success(request, "You've successfully logged out . Come back soon!")
    return redirect('accounts:login')


@login_required(login_url = 'accounts:login')
def dashboard(request):
    orders = Order.objects.filter(user=request.user, is_ordered=True).order_by('-created_at')
    orders_count = orders.count()
    
    # Get counts for different order statuses
    pending_orders = orders.filter(status__in=['New', 'Processing', 'Out_For_Delivery']).count()
    delivered_orders = orders.filter(status='Delivered').count()
    
    recent_orders = orders[:5]  # Get 5 most recent orders
    
    context = {
        'orders_count': orders_count,
        'pending_orders': pending_orders,
        'completed_orders': delivered_orders,
        'recent_orders': recent_orders,
    }
    return render(request, 'shop/accounts/dashboard/dashboard.html', context)



@login_required(login_url = 'accounts:login')
def my_orders(request):
    orders = Order.objects.filter(
        user=request.user,
        is_ordered=True
    ).order_by('-created_at')
    
    context = {
        'orders': orders,
    }
    return render(request, 'shop/accounts/dashboard/my_orders.html', context)


@login_required(login_url = 'accounts:login')
def edit_profile(request):
    userprofile, created = UserProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=request.user)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=userprofile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Your profile has been updated.')
            return redirect('accounts:edit_profile')
    else:
        user_form = UserForm(instance=request.user)
        profile_form = UserProfileForm(instance=userprofile)
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'userprofile': userprofile,
    }
    return render(request, 'shop/accounts/dashboard/edit_profile.html', context)


@login_required(login_url = 'accounts:login')
def change_password(request):
    if request.method == 'POST':
        old_password = request.POST['old_password']
        new_password = request.POST['new_password']
        repeat_new_password = request.POST['repeat_new_password']

        user = Account.objects.get(username__exact=request.user.username)

        if new_password == repeat_new_password:
            success = user.check_password(old_password)
            if success :
                user.set_password(new_password)
                user.save()
                auth.login(request, user)
                messages.success(request, 'Password Updated successfully.')
                return redirect('accounts:change_password')
            else:
                messages.error(request, 'Old password is wrong')
                return redirect('accounts:change_password')
        else:
            messages.error(request, 'Password does not match')
            return redirect('accounts:change_password')

    return render(request, 'shop/accounts/dashboard/change_password.html')


@login_required(login_url = 'accounts:login')
def order_detail(request, order_id):
    try:
        # Get the order and verify ownership
        order = Order.objects.get(order_number=order_id, user=request.user)
        
        # Get order products and calculate totals
        order_detail = OrderProduct.objects.filter(order=order)
        profile = UserProfile.objects.get(user=request.user)
        
        # Calculate subtotal using a generator expression
        subtotal = sum(item.product_price * item.quantity for item in order_detail)

        context = {
            'order_detail': order_detail,
            'order': order,
            'subtotal': subtotal,
            'profile': profile,
        }
        return render(request, 'shop/accounts/dashboard/order_detail.html', context)
    except Order.DoesNotExist:
        messages.error(request, 'Order not found or you do not have permission to view it.')
        return redirect('accounts:my_orders')


def forget_password(request):
    if request.method == 'POST':
        email = request.POST['email']
        try:
            user = Account.objects.get(email=email)
            
            current_site = get_current_site(request)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            
            reset_url = f"{request.scheme}://{current_site.domain}/accounts/resetpassword_validate/{uid}/{token}/"
            
            mail_subject = 'Reset Your Password'
            message = render_to_string('shop/accounts/forget_password/password_reset_email.html', {
                'user': user,
                'reset_url': reset_url,
                'domain': current_site.domain,
            })
            
            try:
                import smtplib
                from email.mime.text import MIMEText
                from email.mime.multipart import MIMEMultipart
                from django.conf import settings

                msg = MIMEMultipart('alternative')
                msg['Subject'] = mail_subject
                msg['From'] = settings.EMAIL_HOST_USER
                msg['To'] = user.email

                html_part = MIMEText(message, 'html')
                msg.attach(html_part)

                with smtplib.SMTP_SSL(settings.EMAIL_HOST, settings.EMAIL_PORT) as server:
                    server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
                    server.send_message(msg)

                messages.success(request, 'Password reset link sent to your email.')
                return redirect('accounts:login')
            except Exception as e:
                messages.error(request, f'Failed to send password reset email. Please try again later.')
                return redirect('accounts:forget_password')
        except Account.DoesNotExist:
            messages.error(request, 'No account found with this email.')
            return redirect('accounts:forget_password')

    return render(request, 'shop/accounts/forget_password/forget_password.html')


def resetpassword_validate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = Account.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, Account.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        request.session['uid'] = uid
        messages.success(request, 'Please reset your password')
        return redirect('accounts:reset_password')
    else:
        messages.error(request, 'This password reset link has expired!')
        return redirect('accounts:forget_password')


def reset_password(request):
    if request.method == 'POST':
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']

        if password == confirm_password:
            uid = request.session.get('uid')
            if uid:
                try:
                    user = Account.objects.get(pk=uid)
                    user.set_password(password)
                    user.save()
                    messages.success(request, 'Password reset successful')
                    return redirect('accounts:login')
                except Account.DoesNotExist:
                    messages.error(request, 'User not found')
                    return redirect('accounts:forget_password')
            else:
                messages.error(request, 'Invalid password reset session')
                return redirect('accounts:forget_password')
        else:
            messages.error(request, 'Passwords do not match!')
            return redirect('accounts:reset_password')

    return render(request, 'shop/accounts/forget_password/reset_password.html')


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@protected_resource()
def user_info(request):
    user = request.user
    return Response({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'is_active': user.is_active
    })