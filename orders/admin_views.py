from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.db.models import Q
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from .models import Order, OrderProduct, DeliveryLocation

@staff_member_required(login_url='admin:login')
def admin_orders_dashboard(request):
    search_query = request.GET.get('search', '')
    
    if search_query:
        orders = Order.objects.filter(order_number__icontains=search_query).order_by('-created_at')
        new_orders = orders.filter(status='Pending')
        processed_orders = orders.filter(status='Delivered')
        processing_orders = orders.filter(Q(status='Processing') | Q(status='Out_For_Delivery'))
    else:
        new_orders = Order.objects.filter(status='Pending').order_by('-created_at')
        processed_orders = Order.objects.filter(status='Delivered').order_by('-created_at')
        processing_orders = Order.objects.filter(
            Q(status='Processing') | Q(status='Out_For_Delivery')
        ).order_by('-created_at')

    # Prefetch related delivery locations to avoid N+1 queries
    new_orders = new_orders.select_related('delivery_location')
    processed_orders = processed_orders.select_related('delivery_location')
    processing_orders = processing_orders.select_related('delivery_location')

    context = {
        'new_orders': new_orders,
        'processed_orders': processed_orders,
        'processing_orders': processing_orders,
        'search_query': search_query,
        'title': 'Orders Management'
    }
    return render(request, 'admin/orders/orders_dashboard.html', context)

@staff_member_required(login_url='admin:login')
def admin_order_detail(request, order_id):
    order = get_object_or_404(Order.objects.select_related('delivery_location'), id=order_id)
    order_products = OrderProduct.objects.filter(order=order)
    
    context = {
        'order': order,
        'order_products': order_products,
        'total_amount': order.get_total_amount(),
        'title': f'Order #{order.order_number}'
    }
    return render(request, 'admin/orders/order_detail.html', context)

@staff_member_required(login_url='admin:login')
def update_order_status(request, order_id):
    if request.method == 'POST':
        order = get_object_or_404(Order, id=order_id)
        new_status = request.POST.get('status')
        if new_status in dict(Order.STATUS):
            order.status = new_status
            order.save()
            
            # Send email notification to customer
            subject = f'Order {order.order_number} Status Update'
            message = f'Your order status has been updated to: {new_status}'
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [order.email],
                fail_silently=True,
            )
            
            messages.success(request, f'Order status updated to {new_status}')
        else:
            messages.error(request, 'Invalid status')
    return redirect('orders:admin_orders_dashboard')
