from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('initiate/<int:order_id>/', views.initiate_payment, name='initiate_payment'),
    path('verify/', views.verify_payment, name='verify_payment'),
    path('status/<int:payment_id>/', views.payment_status, name='payment_status'),
    path('webhook/paystack/', views.paystack_webhook, name='paystack_webhook'),
]
