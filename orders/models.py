from django.db import models
from accounts.models import Account
from shop.models import Product, Variation
from decimal import Decimal


class Payment(models.Model):
    user = models.ForeignKey(Account, on_delete=models.CASCADE)
    payment_id = models.CharField(max_length=100)
    payment_method = models.CharField(max_length=100)
    amount_paid = models.CharField(max_length=100) # this is the total amount paid
    status = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.payment_id


class HubtelMomoPayment(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed')
    ]

    NETWORK_CHOICES = [
        ('mtn', 'MTN Mobile Money'),
        ('vodafone', 'Vodafone Cash'),
        ('airteltigo', 'AirtelTigo Money')
    ]

    user = models.ForeignKey(Account, on_delete=models.CASCADE)
    order = models.ForeignKey('Order', on_delete=models.CASCADE)
    transaction_id = models.CharField(max_length=100, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    phone_number = models.CharField(max_length=15)
    network = models.CharField(max_length=20, choices=NETWORK_CHOICES)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    client_reference = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.network} payment - {self.transaction_id}"


class DeliveryLocation(models.Model):
    name = models.CharField(max_length=100)
    is_tarkwa = models.BooleanField(default=False)
    base_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    distance_km = models.DecimalField(max_digits=10, decimal_places=2, help_text="Distance from Tarkwa in kilometers")
    
    def __str__(self):
        return self.name
    
    def get_delivery_fee(self, order_total):
        if self.is_tarkwa:
            return Decimal('0.00')
        
        # Base delivery fee for locations outside Tarkwa
        fee = self.base_fee
        
        # Add distance-based fee (GH₵2 per km after first 10km)
        if self.distance_km > 10:
            extra_distance = self.distance_km - 10
            fee += extra_distance * Decimal('2.00')
        
        # Discount delivery fee based on order total
        if order_total >= 1000:
            fee *= Decimal('0.5')  # 50% off delivery for orders over GH₵1000
        elif order_total >= 500:
            fee *= Decimal('0.75')  # 25% off delivery for orders over GH₵500
        
        return fee.quantize(Decimal('0.01'))


class Order(models.Model):
    STATUS = (
        ('Pending', 'Pending'),
        ('Processing', 'Processing'),
        ('Out_For_Delivery', 'Out For Delivery'),
        ('Delivered', 'Delivered'),
        ('Cancelled', 'Cancelled'),
    )

    user = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True)
    payment = models.ForeignKey(Payment, on_delete=models.SET_NULL, blank=True, null=True)
    order_number = models.CharField(max_length=20, unique=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    phone = models.CharField(max_length=15)
    email = models.EmailField(max_length=50)
    address = models.CharField(max_length=200)
    country = models.CharField(max_length=50)
    state = models.CharField(max_length=50)
    city = models.CharField(max_length=50)
    order_note = models.CharField(max_length=100, blank=True)
    delivery_location = models.ForeignKey(DeliveryLocation, on_delete=models.SET_NULL, null=True)
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    order_total = models.DecimalField(max_digits=10, decimal_places=2)  
    status = models.CharField(max_length=20, choices=STATUS, default='Pending')
    delivery_date = models.DateTimeField(null=True, blank=True)
    ip = models.CharField(blank=True, max_length=20)
    is_ordered = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def full_name(self):
        return f'{self.first_name} {self.last_name}'

    def order_created(self):
        return self.created_at.strftime('%B %d %Y')

    def hour_update(self):
        return self.created_at.strftime('%H:%M %p')

    def get_total_amount(self):
        return (self.order_total + self.delivery_fee).quantize(Decimal('0.01'))
        
    def __str__(self):
        return self.first_name


class OrderProduct(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    payment = models.ForeignKey(Payment, on_delete=models.SET_NULL, blank=True, null=True)
    user = models.ForeignKey(Account, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variations = models.ManyToManyField(Variation, blank=True)
    quantity = models.IntegerField()
    product_price = models.DecimalField(max_digits=10, decimal_places=2)  
    ordered = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def sub_total(self):
        return (self.quantity * self.product_price).quantize(Decimal('0.01'))

    def order_created(self):
        return self.created_at.strftime('%B %d %Y')

    def __str__(self):
        return self.product.name
