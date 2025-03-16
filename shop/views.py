from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, Count
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings

from .models import Product, Category, ReviewRating, Wishlist, ProductGallery
from cart.views import _cart_id
from cart.models import CartItem
from .forms import ReviewForm, ContactForm
from orders.models import OrderProduct

def home(request):
    products = Product.objects.all().filter(is_available=True)
    featured_products = Product.objects.filter(is_available=True, featured=True)[:6]  # Get up to 6 featured products
    context = {
        'products': products,
        'featured_products': featured_products,
    }
    return render(request, 'shop/index.html', context)

def shop(request, category_slug=None):
    categories = Category.objects.all()
    products = None
    user_wishlist = []

    if category_slug:
        print(f"Looking for category with slug: {category_slug}")  # Debug print
        category = get_object_or_404(Category, slug=category_slug)
        print(f"Found category: {category.name}")  # Debug print
        products = Product.objects.filter(category=category, is_available=True).order_by('-date_joined_for_format')
        print(f"Found {products.count()} products in this category")  # Debug print
        for product in products:
            print(f"Product: {product.name}, Available: {product.is_available}, Stock: {product.stock}")  # Debug print
    else:
        products = Product.objects.all().filter(is_available=True).order_by('-date_joined_for_format')

    if request.user.is_authenticated:
        user_wishlist = Wishlist.objects.filter(user=request.user).values_list('product', flat=True)

    paginator = Paginator(products, 12)
    page = request.GET.get('page')
    try:
        paged_products = paginator.page(page)
    except PageNotAnInteger:
        paged_products = paginator.page(1)
    except EmptyPage:
        paged_products = paginator.page(paginator.num_pages)

    products_count = products.count()

    context = {
        'categories': categories,
        'category_slug': category_slug,
        'products': paged_products,
        'products_count': products_count,
        'user_wishlist': user_wishlist,
    }
    return render(request, 'shop/shop/shop.html', context)

def product_details(request, category_slug, product_details_slug):
    try:
        single_product = Product.objects.get(category__slug=category_slug, slug=product_details_slug)
        
        in_cart = CartItem.objects.filter(cart__cart_id=_cart_id(request), product=single_product).exists()
    except Exception as e:
        return e

    if request.user.is_authenticated:
        try:
            orderproduct = OrderProduct.objects.filter(user=request.user, product_id=single_product.id).exists()
            user_wishlist = Wishlist.objects.filter(user=request.user).values_list('product', flat=True)
        except OrderProduct.DoesNotExist:
            orderproduct = None
            user_wishlist = []
    else:
        orderproduct = None
        user_wishlist = []

    reviews = ReviewRating.objects.order_by('-updated_at').filter(product_id=single_product.id, status=True)
    product_gallery = ProductGallery.objects.filter(product_id=single_product.id)

    context = {
        'single_product': single_product,
        'in_cart': in_cart,
        'orderproduct': orderproduct,
        'reviews': reviews,
        'product_gallery': product_gallery,
        'user_wishlist': user_wishlist,
    }
    return render(request, 'shop/shop/product_details.html', context)


def search(request):
    products = None
    products_count = 0
    categories = Category.objects.all()
    
    if 'keyword' in request.GET:
        keyword = request.GET['keyword'].strip()
        if keyword:
            # Create a Q object for the search
            query = Q()
            
            # Split search terms and remove empty strings
            search_terms = [term.lower() for term in keyword.split() if term.strip()]
            
            for term in search_terms:
                # Primary search fields (exact matches get higher priority)
                name_exact = Q(name__iexact=term)
                category_exact = Q(category__name__iexact=term)
                
                # Secondary search fields (contains)
                name_contains = Q(name__icontains=term)
                description_contains = Q(description__icontains=term)
                features_contains = Q(features__icontains=term)
                material_contains = Q(material__icontains=term)
                category_contains = Q(category__name__icontains=term)
                certifications_contains = Q(certifications__icontains=term)
                
                # Combine all search conditions
                term_query = (
                    name_exact | category_exact |  # Exact matches
                    name_contains | description_contains |  # Partial matches
                    features_contains | material_contains |
                    category_contains | certifications_contains
                )
                
                query |= term_query
            
            # Get available products matching the query
            products = Product.objects.filter(query, is_available=True).distinct()
            
            # Order results by relevance
            products = products.annotate(
                name_matches=Count('id', filter=Q(name__icontains=keyword)),
                category_matches=Count('id', filter=Q(category__name__icontains=keyword))
            ).order_by('-name_matches', '-category_matches', 'name')
            
            products_count = products.count()
            
            # If no results found with exact/contains, try fuzzy matching
            if products_count == 0:
                for term in search_terms:
                    if len(term) >= 3:
                        # Try matching with first few characters
                        partial_query = (
                            Q(name__istartswith=term[:3]) |
                            Q(description__icontains=term[:3]) |
                            Q(category__name__istartswith=term[:3])
                        )
                        fuzzy_products = Product.objects.filter(
                            partial_query, 
                            is_available=True
                        ).distinct()
                        
                        if fuzzy_products.exists():
                            products = fuzzy_products
                            products_count = fuzzy_products.count()
                            break
    
    context = {
        'products': products,
        'products_count': products_count,
        'search_keyword': keyword if 'keyword' in request.GET else '',
        'categories': categories,
    }
    return render(request, 'shop/shop/search.html', context)



def review(request, product_id):
    url = request.META.get('HTTP_REFERER')
    if request.method == 'POST':
        try:
            # Check if user has already reviewed
            review = ReviewRating.objects.get(user=request.user, product_id=product_id)
            form = ReviewForm(request.POST, instance=review)
            if form.is_valid():
                form.save()
                messages.success(request, 'Thank you! Your review has been updated.')
            else:
                messages.error(request, 'Please check your review. The review must be at least 10 characters long and rating must be between 1-5 stars.')
            return redirect(url)
        except ReviewRating.DoesNotExist:
            form = ReviewForm(request.POST)
            if form.is_valid():
                data = ReviewRating()
                data.rating = form.cleaned_data['rating']
                data.review = form.cleaned_data['review']
                data.ip = request.META.get('REMOTE_ADDR')
                data.product_id = product_id
                data.user_id = request.user.id
                data.save()
                messages.success(request, 'Thank you! Your review has been submitted.')
            else:
                messages.error(request, 'Please check your review. The review must be at least 10 characters long and rating must be between 1-5 stars.')
            return redirect(url)
    
    messages.error(request, 'Invalid request method.')
    return redirect(url)

@login_required
def add_to_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    wishlist_item, created = Wishlist.objects.get_or_create(user=request.user, product=product)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        if not created:
            wishlist_item.delete()
            return JsonResponse({
                'status': 'success',
                'created': False,
                'message': f'Removed {product.name} from wishlist'
            })
        else:
            return JsonResponse({
                'status': 'success',
                'created': True,
                'message': f'Added {product.name} to wishlist'
            })
    
    # For non-AJAX requests
    if not created:
        wishlist_item.delete()
        messages.success(request, f'{product.name} removed from your wishlist')
    else:
        messages.success(request, f'{product.name} added to your wishlist')

    # Get the referring page
    referer = request.META.get('HTTP_REFERER', '')
    return redirect(referer or 'shop:shop')

@login_required
def view_wishlist(request):
    wishlist_items = Wishlist.objects.filter(user=request.user).select_related('product')
    context = {
        'wishlist_items': wishlist_items
    }
    return render(request, 'shop/shop/wishlist.html', context)

def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            subject = form.cleaned_data['subject']
            message = form.cleaned_data['message']
            
            # Send email to admin
            email_message = f"""
            Name: {name}
            Email: {email}
            Subject: {subject}
            Message: {message}
            """
            
            try:
                send_mail(
                    f'Contact Form: {subject}',
                    email_message,
                    settings.DEFAULT_FROM_EMAIL,
                    [settings.DEFAULT_FROM_EMAIL],
                    fail_silently=False,
                )
                messages.success(request, 'Thank you for contacting us. We will get back to you soon.')
            except Exception as e:
                messages.error(request, 'Sorry, there was an error sending your message. Please try again later.')
            
            return redirect('contact')
    
    return render(request, 'contact.html')
