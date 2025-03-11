from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.crypto import get_random_string
from django.conf import settings
from .models import MobileMoneyPayment
from orders.models import Order, OrderProduct
from cart.models import CartItem
import requests
import json
import hmac
import hashlib
from django.http import HttpResponse
from django.urls import reverse
from django.shortcuts import get_object_or_404
import time
from django.views.decorators.csrf import csrf_exempt

# Create your views here.

@login_required
def initiate_payment(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    if request.method == 'POST':
        phone_number = request.POST.get('phone_number')
        network = request.POST.get('network')
        
        if not phone_number or not network:
            messages.error(request, 'Please provide both phone number and network')
            return redirect('payments:initiate_payment', order_id=order_id)
            
        # Initialize Paystack payment
        paystack_secret = settings.PAYSTACK_SECRET_KEY
        url = 'https://api.paystack.co/transaction/initialize'
        
        # Convert amount to pesewas
        amount_pesewas = int(order.order_total * 100)
        
        # Map network providers to Paystack channel codes
        network_map = {
            'MTN': 'mtn',
            'VODAFONE': 'vod',
            'AIRTELTIGO': 'tgo'
        }
        
        channel = network_map.get(network.upper())
        if not channel:
            messages.error(request, 'Invalid network selected')
            return redirect('payments:initiate_payment', order_id=order_id)
        
        headers = {
            'Authorization': f'Bearer {paystack_secret}',
            'Content-Type': 'application/json',
        }
        
        data = {
            'email': request.user.email,
            'amount': amount_pesewas,
            'currency': 'GHS',
            'mobile_money': {
                'phone': phone_number,
                'provider': channel
            },
            'channels': ['mobile_money'],
            'callback_url': request.build_absolute_uri(reverse('payments:verify_payment')),
            'reference': f'order_{order.id}_{int(time.time())}',
            'metadata': {
                'order_id': order.id,
                'phone_number': phone_number,
                'network': network,
                'custom_fields': [
                    {
                        'display_name': 'Order Number',
                        'variable_name': 'order_number',
                        'value': order.order_number
                    }
                ]
            }
        }
        
        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            
            result = response.json()
            
            if result['status']:
                # Store payment details
                payment = MobileMoneyPayment.objects.create(
                    order=order,
                    amount=order.order_total,
                    phone_number=phone_number,
                    network=network,
                    reference=result['data']['reference'],
                    status='PENDING'
                )
                
                # Redirect to Paystack payment page
                return redirect(result['data']['authorization_url'])
            else:
                messages.error(request, 'Could not initialize payment. Please try again.')
                return redirect('orders:payment_method')
                
        except requests.exceptions.RequestException as e:
            messages.error(request, 'Payment service is currently unavailable. Please try again later.')
            return redirect('orders:payment_method')
    
    return render(request, 'payments/momo_payment.html', {'order': order})

@login_required
def initiate_paystack_payment(request, order_id):
    try:
        order = Order.objects.get(id=order_id, user=request.user)
        
        if request.method == 'POST':
            phone_number = request.POST.get('phone_number')
            network = request.POST.get('network')
            
            if not phone_number or not network:
                messages.error(request, 'Please provide both phone number and network')
                return redirect('payments:initiate_payment', order_id=order_id)
            
            # Generate unique reference
            reference = f"SHERIMANDY-{get_random_string(8).upper()}"
            
            # Prepare Paystack API request
            url = "https://api.paystack.co/charge"
            
            headers = {
                "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "amount": int(order.order_total * 100),  # Convert to pesewas
                "email": request.user.email,
                "currency": "GHS",
                "mobile_money": {
                    "phone": phone_number,
                    "provider": network.lower()
                },
                "reference": reference
            }
            
            # Make request to Paystack
            response = requests.post(url, headers=headers, json=payload)
            
            if response.status_code == 200:
                response_data = response.json()
                
                if response_data['status']:
                    # Create payment record
                    payment = MobileMoneyPayment.objects.create(
                        order=order,
                        amount=order.order_total,
                        phone_number=phone_number,
                        network=network,
                        reference=reference,
                        status='PENDING'
                    )
                    
                    messages.success(
                        request, 
                        'Please check your phone to authorize the payment.'
                    )
                    return redirect('payments:payment_status', payment_id=payment.id)
                else:
                    messages.error(request, response_data['message'])
            else:
                messages.error(request, 'Failed to initiate payment. Please try again.')
            
            return redirect('payments:initiate_payment', order_id=order_id)
            
        return render(request, 'payments/momo_payment.html', {
            'order': order,
            'networks': [
                ('MTN', 'MTN Mobile Money'),
                ('VODAFONE', 'Vodafone Cash'),
                ('AIRTELTIGO', 'AirtelTigo Money')
            ],
            'paystack_public_key': settings.PAYSTACK_PUBLIC_KEY
        })
        
    except Order.DoesNotExist:
        messages.error(request, 'Order not found')
        return redirect('orders:order_list')

@login_required
def payment_status(request, payment_id):
    try:
        payment = MobileMoneyPayment.objects.get(id=payment_id, order__user=request.user)
        return render(request, 'payments/payment_status.html', {'payment': payment})
    except MobileMoneyPayment.DoesNotExist:
        messages.error(request, 'Payment not found')
        return redirect('orders:order_list')

@csrf_exempt
def verify_payment(request):
    # Get the payment reference from the query parameters
    reference = request.GET.get('reference')
    if not reference:
        messages.error(request, 'No payment reference provided')
        return redirect('orders:payment_method')
    
    try:
        # Verify the payment with Paystack
        paystack_secret = settings.PAYSTACK_SECRET_KEY
        url = f'https://api.paystack.co/transaction/verify/{reference}'
        
        headers = {
            'Authorization': f'Bearer {paystack_secret}',
        }
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        result = response.json()
        
        if result['status'] and result['data']['status'] == 'success':
            # Get the metadata from the response
            metadata = result['data']['metadata']
            order_id = metadata['order_id']
            
            # Update the order and payment status
            try:
                payment = MobileMoneyPayment.objects.get(reference=reference)
                if payment.status != 'COMPLETED':
                    payment.status = 'COMPLETED'
                    payment.save()
                    
                    order = payment.order
                    if not order.is_ordered:
                        order.is_ordered = True
                        order.save()
                        
                        # Move cart items to order products
                        cart_items = CartItem.objects.filter(user=request.user)
                        for cart_item in cart_items:
                            order_product = OrderProduct()
                            order_product.order = order
                            order_product.payment = payment
                            order_product.user = request.user
                            order_product.product = cart_item.product
                            order_product.quantity = cart_item.quantity
                            order_product.product_price = cart_item.product.price
                            order_product.ordered = True
                            order_product.save()
                            
                            # Add product variations to order product
                            if cart_item.variation.exists():
                                order_product.variations.set(cart_item.variation.all())
                        
                        # Clear the user's cart after successful payment
                        cart_items.delete()
                    
                    messages.success(request, 'Payment completed successfully!')
                    return redirect('orders:order_detail', order_id=order.id)
                    
            except MobileMoneyPayment.DoesNotExist:
                messages.error(request, 'Payment record not found')
                return redirect('orders:payment_method')
        else:
            messages.error(request, 'Payment verification failed')
            return redirect('orders:payment_method')
            
    except requests.exceptions.RequestException as e:
        messages.error(request, 'Could not verify payment. Please contact support.')
        return redirect('orders:payment_method')

def paystack_webhook(request):
    if request.method != 'POST':
        return HttpResponse(status=405)
    
    # Verify webhook signature
    paystack_signature = request.headers.get('x-paystack-signature')
    if not paystack_signature:
        return HttpResponse(status=400)
    
    # Get the request body
    payload = request.body
    
    # Verify the event
    computed_hmac = hmac.new(
        settings.PAYSTACK_SECRET_KEY.encode('utf-8'),
        payload,
        hashlib.sha512
    ).hexdigest()
    
    if computed_hmac != paystack_signature:
        return HttpResponse(status=400)
    
    # Process the webhook
    event = json.loads(payload)
    
    if event['event'] == 'charge.success':
        reference = event['data']['reference']
        try:
            payment = MobileMoneyPayment.objects.get(reference=reference)
            payment.status = 'COMPLETED'
            payment.transaction_id = event['data']['id']
            payment.save()
            
            # Update order status
            order = payment.order
            if not order.is_ordered:
                order.is_ordered = True
                order.paid = True
                order.save()
                
                # Move cart items to order products
                cart_items = CartItem.objects.filter(user=order.user)
                for cart_item in cart_items:
                    order_product = OrderProduct()
                    order_product.order = order
                    order_product.payment = payment
                    order_product.user = order.user
                    order_product.product = cart_item.product
                    order_product.quantity = cart_item.quantity
                    order_product.product_price = cart_item.product.price
                    order_product.ordered = True
                    order_product.save()
                    
                    # Add product variations to order product
                    if cart_item.variation.exists():
                        order_product.variations.set(cart_item.variation.all())
                
                # Clear the user's cart after successful payment
                cart_items.delete()
            
        except MobileMoneyPayment.DoesNotExist:
            return HttpResponse(status=404)
    
    return HttpResponse(status=200)
