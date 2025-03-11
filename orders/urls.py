from django.urls import path
from . import views, admin_views

app_name = 'orders'

urlpatterns = [
    # Main order URLs
    path('', views.payment_method, name='orders_home'),
    path('checkout/', views.checkout, name='checkout'),
    path('order_completed/', views.order_completed, name='order_completed'),
    path('order/<int:order_id>/', views.order_detail, name='order_detail'),
    
    # Payment URLs
    path('payment_method/', views.payment_method, name='payment_method'),
    path('payment-complete/', views.payment_complete, name='payment_complete'),
    path('payment-cancelled/', views.payment_cancelled, name='payment_cancelled'),
    path('paystack-webhook/', views.paystack_webhook, name='paystack_webhook'),
    
    # Delivery fee API
    path('get_delivery_fee/<int:location_id>/', views.get_delivery_fee, name='get_delivery_fee'),
    
    # Admin URLs
    path('admin/orders/', admin_views.admin_orders_dashboard, name='admin_orders_dashboard'),
    path('admin/orders/<int:order_id>/', admin_views.admin_order_detail, name='admin_order_detail'),
    path('admin/orders/<int:order_id>/update-status/', admin_views.update_order_status, name='admin_update_order_status'),
]
