from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse, HttpResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.db import transaction
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.urls import reverse

from cart.models import CartItem, Cart
from cart.views import _cart_id
from .forms import OrderForm
from .models import Order, Payment, OrderProduct, DeliveryLocation
from shop.models import Product, Wishlist

import datetime
import json
import hmac
import hashlib
import base64
from decimal import Decimal
import requests
import random

@login_required(login_url='accounts:login')
def payment_method(request):
    return render(request, 'shop/orders/payment_method.html')

@login_required(login_url='accounts:login')
def checkout(request, total=0, total_price=0, quantity=0, cart_items=None):
    try:
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user, is_active=True)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)
        
        for cart_item in cart_items:
            total_price += cart_item.sub_total()
            quantity += cart_item.quantity
        
        grand_total = total_price

        if request.method == 'POST':
            form = OrderForm(request.POST)
            if form.is_valid():
                order = Order()
                order.user = request.user
                order.first_name = form.cleaned_data['first_name']
                order.last_name = form.cleaned_data['last_name']
                order.phone = form.cleaned_data['phone']
                order.email = form.cleaned_data['email']
                order.address = form.cleaned_data['address']
                order.country = form.cleaned_data['country']
                order.state = form.cleaned_data['state']
                order.city = form.cleaned_data['city']
                order.order_note = form.cleaned_data['order_note']
                
                # Handle delivery location
                delivery_location_id = request.POST.get('delivery_location')
                if delivery_location_id:
                    delivery_location = get_object_or_404(DeliveryLocation, id=delivery_location_id)
                    order.delivery_location = delivery_location
                    order.delivery_fee = delivery_location.get_delivery_fee(total_price)
                    grand_total += order.delivery_fee
                
                order.order_total = grand_total
                order.ip = request.META.get('REMOTE_ADDR')
                order.save()

                # Generate order number
                yr = int(datetime.date.today().strftime('%Y'))
                dt = int(datetime.date.today().strftime('%d'))
                mt = int(datetime.date.today().strftime('%m'))
                d = datetime.date(yr, mt, dt)
                current_date = d.strftime("%Y%m%d")
                
                # Add random suffix to ensure uniqueness
                random_num = ''.join([str(random.randint(0, 9)) for _ in range(4)])
                order_number = current_date + random_num
                
                while Order.objects.filter(order_number=order_number).exists():
                    random_num = ''.join([str(random.randint(0, 9)) for _ in range(4)])
                    order_number = current_date + random_num
                
                order.order_number = order_number
                order.save()

                # Create payment record
                payment = Payment.objects.create(
                    user=request.user,
                    payment_id=f"PAY-{order_number}",
                    payment_method="Paystack",
                    amount_paid=str(grand_total),
                    status='pending'
                )
                
                order.payment = payment
                order.save()

                # Redirect to Paystack payment
                headers = {
                    'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}',
                    'Content-Type': 'application/json'
                }
                
                payload = {
                    'email': order.email,
                    'amount': int(grand_total * 100),
                    'currency': 'GHS',
                    'callback_url': request.build_absolute_uri('/orders/payment-complete/'),
                    'metadata': {
                        'order_id': order.id,
                        'order_number': order_number,
                        'customer_name': f"{order.first_name} {order.last_name}",
                        'customer_phone': order.phone,
                        'delivery_location': order.delivery_location.name if order.delivery_location else 'Not specified'
                    }
                }

                response = requests.post(
                    'https://api.paystack.co/transaction/initialize',
                    json=payload,
                    headers=headers
                )

                if response.status_code == 200:
                    response_data = response.json()
                    payment.payment_id = response_data['data']['reference']
                    payment.save()
                    return redirect(response_data['data']['authorization_url'])
                else:
                    messages.error(request, 'Payment initialization failed')
                    return redirect('orders:checkout')

    except ObjectDoesNotExist:
        pass

    delivery_locations = DeliveryLocation.objects.all()
    context = {
        'total_price': total_price,
        'quantity': quantity,
        'cart_items': cart_items,
        'delivery_locations': delivery_locations,
        'grand_total': grand_total,
    }
    return render(request, 'shop/orders/checkout/checkout.html', context)

@login_required(login_url='accounts:login')
def payment_complete(request):
    try:
        # Get payment reference from URL parameters
        reference = request.GET.get('reference', '')
        if not reference:
            messages.error(request, 'No payment reference found')
            return redirect('cart:cart')

        # Verify payment status with Paystack
        headers = {
            'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}'
        }
        response = requests.get(
            f'https://api.paystack.co/transaction/verify/{reference}',
            headers=headers
        )

        if response.status_code == 200:
            response_data = response.json()
            if response_data['data']['status'] == 'success':
                # Update payment and order
                payment = Payment.objects.get(payment_id=reference)
                payment.status = 'completed'
                payment.save()

                order = Order.objects.get(payment=payment)
                order.is_ordered = True
                order.status = 'Pending'  # Set initial status to Pending
                order.save()

                # Move cart items to order products and clear cart
                cart_items = CartItem.objects.filter(user=request.user)
                for item in cart_items:
                    OrderProduct.objects.create(
                        order=order,
                        payment=payment,
                        user=request.user,
                        product=item.product,
                        quantity=item.quantity,
                        product_price=item.product.get_discounted_price(),
                        ordered=True
                    )
                    
                    # Reduce stock
                    product = item.product
                    product.stock -= item.quantity
                    product.save()
                    
                    # Remove from wishlist if present
                    Wishlist.objects.filter(user=request.user, product=item.product).delete()
                
                # Clear cart
                cart_items.delete()
                
                messages.success(request, 'Payment completed successfully')
                return redirect('orders:order_completed')
            else:
                messages.error(request, 'Payment verification failed')
                return redirect('cart:cart')
        else:
            messages.error(request, 'Could not verify payment')
            return redirect('cart:cart')

    except Exception as e:
        messages.error(request, 'An error occurred while processing your payment')
        return redirect('cart:cart')

def payment_cancelled(request):
    messages.error(request, 'Payment was cancelled')
    return redirect('cart:cart')

@csrf_exempt
@require_POST
def paystack_webhook(request):
    paystack_signature = request.headers.get('x-paystack-signature')
    if not paystack_signature:
        return HttpResponse(status=400)
    
    # Read and verify payload
    payload = request.body
    computed_hmac = hmac.new(
        settings.PAYSTACK_SECRET_KEY.encode('utf-8'),
        payload,
        hashlib.sha512
    ).hexdigest()
    
    if computed_hmac != paystack_signature:
        return HttpResponse(status=401)
    
    # Process the webhook payload
    try:
        with transaction.atomic():
            event = json.loads(payload)
            if event['event'] == 'charge.success':
                # Get payment details
                reference = event['data']['reference']
                payment = Payment.objects.get(payment_id=reference)
                
                # Update payment status
                payment.status = 'completed'
                payment.save()
                
                # Get the order from metadata
                order_id = event['data']['metadata']['order_id']
                order = Order.objects.get(id=order_id)
                
                # Update order status
                order.payment = payment
                order.is_ordered = True
                order.status = 'Pending'  # Set initial status to Pending
                order.save()
                
                # Get all cart items
                cart_items = CartItem.objects.filter(user=order.user)
                
                # Create order products and update inventory
                for item in cart_items:
                    OrderProduct.objects.create(
                        order=order,
                        payment=payment,
                        user=order.user,
                        product=item.product,
                        quantity=item.quantity,
                        product_price=item.product.get_discounted_price(),
                        ordered=True
                    )
                    
                    # Reduce product stock
                    product = item.product
                    product.stock -= item.quantity
                    product.save()
                    
                    # Remove item from wishlist if it exists
                    Wishlist.objects.filter(user=order.user, product=item.product).delete()
                
                # Clear cart
                cart_items.delete()
                
                return HttpResponse(status=200)
            
            return HttpResponse(status=200)
            
    except Exception as e:
        return HttpResponse(status=500)

@login_required(login_url='accounts:login')
def order_completed(request):
    try:
        # Get the latest completed order for this user
        order = Order.objects.filter(
            user=request.user,
            is_ordered=True,
            status='Completed'
        ).latest('created_at')
        
        # Get order products and calculate totals
        order_products = OrderProduct.objects.filter(order=order).select_related('product')
        
        subtotal = 0
        for item in order_products:
            item.quantity_total = item.quantity * item.product_price
            subtotal += item.quantity_total
        
        context = {
            'order': order,
            'order_products': order_products,
            'subtotal': subtotal,
        }
        
        return render(request, 'shop/orders/order_completed.html', context)
    except Order.DoesNotExist:
        return redirect('shop:shop')

@login_required(login_url='accounts:login')
def order_detail(request, order_id):
    try:
        order = Order.objects.get(id=order_id, user=request.user)
        order_products = OrderProduct.objects.filter(order=order)
        
        # Calculate subtotal
        subtotal = sum(item.product_price * item.quantity for item in order_products)
        
        context = {
            'order': order,
            'order_products': order_products,
            'subtotal': subtotal,
        }
        return render(request, 'shop/orders/order_detail.html', context)
    except Order.DoesNotExist:
        messages.error(request, 'Order not found')
        return redirect('orders:orders_home')

@login_required(login_url='accounts:login')
def get_delivery_fee(request, location_id):
    try:
        location = DeliveryLocation.objects.get(id=location_id)
        total_price = Decimal(request.GET.get('total', 0))
        fee = location.get_delivery_fee(total_price)
        return JsonResponse({'delivery_fee': str(fee)})
    except DeliveryLocation.DoesNotExist:
        return JsonResponse({'error': 'Location not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)