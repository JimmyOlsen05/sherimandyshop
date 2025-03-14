from django.db import models
from django.urls import reverse
from accounts.models import Account
from django.db.models import Avg, Count


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(max_length=250, blank=True)
    image = models.ImageField(upload_to='categories', blank=True)

    class Meta:
        verbose_name = 'Category'
        verbose_name_plural = 'categories'

    def get_category_slug_url(self):
        return reverse('shop:categories', args=[self.slug])

    def __str__(self):
        return self.name


class SafetyStandard(models.Model):
    name = models.CharField(max_length=50)  # e.g., EN166, ANSI Z87.1
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Product(models.Model):
    CERTIFICATION_CHOICES = [
        ('CE', 'CE Certified'),
        ('ANSI', 'ANSI Certified'),
        ('ISO', 'ISO Certified'),
        ('OSHA', 'OSHA Compliant'),
    ]

    SIZE_UNIT_CHOICES = [
        ('US', 'US Size'),
        ('UK', 'UK Size'),
        ('EU', 'EU Size'),
        ('UNIVERSAL', 'Universal Size'),
    ]

    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(max_length=500, blank=True)
    features = models.TextField(blank=True, help_text="Key features and specifications of the PPE")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, help_text="Discount percentage (0-100)")
    image = models.ImageField(upload_to='photos/products')
    stock = models.IntegerField()
    
    # PPE specific fields
    certifications = models.CharField(max_length=20, choices=CERTIFICATION_CHOICES, blank=True)
    safety_standards = models.ManyToManyField(SafetyStandard, blank=True)
    material = models.CharField(max_length=100, blank=True, help_text="Main material of the PPE")
    size_unit = models.CharField(max_length=20, choices=SIZE_UNIT_CHOICES, default='UNIVERSAL')
    weight = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, help_text="Weight in kg")
    color_options = models.CharField(max_length=200, blank=True, help_text="Available colors separated by commas")
    
    # Product status
    new = models.BooleanField(default=False)
    is_available = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)  # New field for featured products
    featured = models.BooleanField(default=False)
    minimum_order = models.IntegerField(default=1, help_text="Minimum order quantity")

    date_joined_for_format = models.DateTimeField(auto_now_add=True)
    last_login_for_format = models.DateTimeField(auto_now=True)

    def created(self):
        return self.date_joined_for_format.strftime('%B %d %Y')

    def updated(self):
        return self.last_login_for_format.strftime('%B %d %Y')

    def __str__(self):
        return self.name
    
    def averageRating(self):
        reviews = ReviewRating.objects.filter(product=self, status=True).aggregate(average=Avg('rating'))
        avg = 0
        if reviews['average'] is not None:
            avg = float(reviews['average'])
        return avg
    
    def countReview(self):
        reviews = ReviewRating.objects.filter(product=self, status=True).aggregate(count=Count('id'))
        count = 0
        if reviews['count'] is not None:
            count = int(reviews['count'])
        return count

    def get_prodcut_details_url(self):
        return reverse('shop:product_details', args=[self.category.slug, self.slug])
    
    def get_discounted_price(self):
        from decimal import Decimal
        if self.discount > 0:
            discount_amount = (self.price * (self.discount / Decimal('100.0'))).quantize(Decimal('0.01'))
            return (self.price - discount_amount).quantize(Decimal('0.01'))
        return self.price

    def get_discount_amount(self):
        from decimal import Decimal
        if self.discount > 0:
            return (self.price * (self.discount / Decimal('100.0'))).quantize(Decimal('0.01'))
        return Decimal('0.00')

    class Meta:
        verbose_name_plural = 'Products'
        ordering = ('-date_joined_for_format',)


class VariationManager(models.Manager):
    def colors(self):
        return super(VariationManager, self).filter(variation_category='color', is_active=True)

    def sizes(self):
        return super(VariationManager, self).filter(variation_category='size', is_active=True)


variation_category_choices = (
    ('color', 'color'),
    ('size', 'size'),
)


class Variation(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variation_category = models.CharField(max_length=100, choices=variation_category_choices)
    variation_value = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)
    objects = VariationManager()

    def __str__(self):
        return self.variation_value


class ReviewRating(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    user = models.ForeignKey(Account, on_delete=models.CASCADE)
    review = models.TextField(max_length=700, blank=True)
    rating = models.FloatField()
    ip = models.CharField(max_length=20, blank=True)
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.rating} Stars - {self.product.name}'


class ProductGallery(models.Model):
    product = models.ForeignKey(Product, default=None, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='product_gallery')

    class Meta:
        verbose_name = 'productgallery'
        verbose_name_plural = 'product gallery'

    def __str__(self):
        return self.product.name


class Wishlist(models.Model):
    user = models.ForeignKey(Account, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    added_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')  # Prevent duplicate wishlist items
        
    def __str__(self):
        return f"{self.user.username}'s wishlist - {self.product.name}"
