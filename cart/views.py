from django.shortcuts import render, redirect, get_object_or_404
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required

from .models import Cart, CartItem
from shop.models import Product
from shop.models import Variation
from orders.models import Order, OrderProduct


def _cart_id(request):
    cart = request.session.session_key
    if not cart:
        cart = request.session.create()
    return cart


def add_cart(request, product_id):
    current_user = request.user
    product = Product.objects.get(id=product_id)
    
    if current_user.is_authenticated:
        product_variation = []
        if request.method == 'POST':
            for item in request.POST:
                key = item
                value = request.POST[key]
                try:
                    variation = Variation.objects.get(product=product, variation_category__iexact=key, variation_value__iexact=value)
                    product_variation.append(variation)
                except:
                    pass
                    
        cart_item = CartItem.objects.filter(product=product, user=current_user).first()
        
        if cart_item:
            # Check if this variation exists
            if product_variation:
                if cart_item.variation.all():
                    ex_var_list = list(cart_item.variation.all())
                    if product_variation == ex_var_list:
                        cart_item.quantity += 1  # Increment quantity instead of setting to 1
                        cart_item.save()
                    else:
                        cart_item = CartItem.objects.create(
                            product=product,
                            quantity=1,
                            user=current_user
                        )
                        cart_item.variation.add(*product_variation)
                else:
                    cart_item.variation.add(*product_variation)
            else:
                cart_item.quantity += 1  # Increment quantity instead of setting to 1
                cart_item.save()
        else:
            cart_item = CartItem.objects.create(
                product=product,
                quantity=1,
                user=current_user
            )
            if product_variation:
                cart_item.variation.add(*product_variation)

        return redirect('cart:cart')

    else:
        product_variation = []
        if request.method == 'POST':
            for item in request.POST:
                key = item
                value = request.POST[key]
                try:
                    variation = Variation.objects.get(product=product, variation_category__iexact=key, variation_value__iexact=value)
                    product_variation.append(variation)
                except:
                    pass

        try:
            cart = Cart.objects.get(cart_id=_cart_id(request))
        except Cart.DoesNotExist:
            cart = Cart.objects.create(cart_id=_cart_id(request))
        cart.save()

        cart_item = CartItem.objects.filter(product=product, cart=cart).first()
        
        if cart_item:
            if product_variation:
                if cart_item.variation.all():
                    ex_var_list = list(cart_item.variation.all())
                    if product_variation == ex_var_list:
                        cart_item.quantity += 1  # Increment quantity instead of setting to 1
                        cart_item.save()
                    else:
                        cart_item = CartItem.objects.create(
                            product=product,
                            quantity=1,
                            cart=cart
                        )
                        cart_item.variation.add(*product_variation)
                else:
                    cart_item.variation.add(*product_variation)
            else:
                cart_item.quantity += 1  # Increment quantity instead of setting to 1
                cart_item.save()
        else:
            cart_item = CartItem.objects.create(
                product=product,
                quantity=1,
                cart=cart
            )
            if product_variation:
                cart_item.variation.add(*product_variation)

        return redirect('cart:cart')


def remove_cart(request, product_id, cart_item_id):
    product = get_object_or_404(Product, id=product_id)
    try:
        if request.user.is_authenticated:
            cart_item = CartItem.objects.get(product=product, user=request.user, id=cart_item_id)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_item = CartItem.objects.get(product=product, cart=cart, id=cart_item_id)
        if cart_item.quantity > 1 :
            cart_item.quantity -= 1
            cart_item.save()
        else :
            cart_item.delete()
    except:
        pass

    return redirect('cart:cart')


def remove_cart_item(request, product_id, cart_item_id):
    try:
        product = get_object_or_404(Product, id=product_id)
        if request.user.is_authenticated:
            cart_item = CartItem.objects.get(product=product, user=request.user, id=cart_item_id)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_item = CartItem.objects.get(product=product, cart=cart, id=cart_item_id)
        cart_item.delete()
    except (CartItem.DoesNotExist, Product.DoesNotExist):
        pass
    return redirect('cart:cart')

@login_required(login_url='accounts:login')
def cart(request, total=0, quantity=0, cart_items=None):
    try:
        tax = 0
        grand_total = 0
        savings = 0
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user, is_active=True)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)
        
        for cart_item in cart_items:
            if cart_item.product.discount > 0:
                item_price = cart_item.product.get_discounted_price()
                original_price = cart_item.product.price
                savings += (original_price - item_price) * cart_item.quantity
            else:
                item_price = cart_item.product.price
            
            total += (item_price * cart_item.quantity)
            quantity += cart_item.quantity
            
        tax = (2 * total)/100
        grand_total = total + tax
    except ObjectDoesNotExist:
        pass

    context = {
        'total': total,
        'quantity': quantity,
        'cart_items': cart_items,
        'tax': tax,
        'grand_total': grand_total,
        'savings': savings,
    }
    return render(request, 'shop/cart/cart.html', context)
