from django.db import models
from django.conf import settings
from orders.models import Order

# Create your models here.

class MobileMoneyPayment(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    ]

    NETWORK_CHOICES = [
        ('MTN', 'MTN Mobile Money'),
        ('VODAFONE', 'Vodafone Cash'),
        ('AIRTELTIGO', 'AirtelTigo Money'),
    ]

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='momo_payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    phone_number = models.CharField(max_length=15)
    network = models.CharField(max_length=20, choices=NETWORK_CHOICES)
    reference = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='PENDING')
    transaction_id = models.CharField(max_length=100, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.network} Payment - {self.reference}"

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Mobile Money Payment'
        verbose_name_plural = 'Mobile Money Payments'
