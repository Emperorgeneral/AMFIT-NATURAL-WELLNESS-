from decimal import Decimal
from random import randint

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from products.models import Product

from .forms import CheckoutForm
from .models import Cart, CartItem, Order, OrderItem


def _get_or_create_cart(user):
    cart, _ = Cart.objects.get_or_create(user=user)
    return cart


def _build_order_number():
    timestamp = timezone.now().strftime('%Y%m%d%H%M')
    return f'AMF-{timestamp}{randint(100, 999)}'


@login_required
def add_to_cart(request, slug):
    if request.method != 'POST':
        return redirect('products:product_detail', slug=slug)

    product = get_object_or_404(Product, slug=slug, status='active')
    quantity = max(int(request.POST.get('quantity', 1)), 1)
    cart = _get_or_create_cart(request.user)

    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if created:
        cart_item.quantity = quantity
    else:
        cart_item.quantity += quantity
    cart_item.save()

    messages.success(request, f'{product.name} added to your cart.')
    return redirect('orders:cart_detail')


@login_required
def cart_detail(request):
    cart = _get_or_create_cart(request.user)
    cart_items = cart.items.select_related('product').all()
    subtotal = sum((item.total for item in cart_items), Decimal('0.00'))
    shipping = Decimal('0.00') if subtotal >= Decimal('25000.00') or subtotal == 0 else Decimal('2500.00')
    tax = (subtotal * Decimal('0.075')).quantize(Decimal('0.01'))
    total = subtotal + shipping + tax

    context = {
        'cart': cart,
        'cart_items': cart_items,
        'subtotal': subtotal,
        'shipping': shipping,
        'tax': tax,
        'total': total,
    }
    return render(request, 'orders/cart.html', context)


@login_required
def update_cart_item(request, item_id):
    if request.method != 'POST':
        return redirect('orders:cart_detail')

    cart = _get_or_create_cart(request.user)
    item = get_object_or_404(CartItem, id=item_id, cart=cart)
    quantity = int(request.POST.get('quantity', 1))

    if quantity <= 0:
        item.delete()
        messages.success(request, 'Item removed from your cart.')
    else:
        item.quantity = quantity
        item.save()
        messages.success(request, 'Cart updated successfully.')

    return redirect('orders:cart_detail')


@login_required
def remove_cart_item(request, item_id):
    if request.method != 'POST':
        return redirect('orders:cart_detail')

    cart = _get_or_create_cart(request.user)
    item = get_object_or_404(CartItem, id=item_id, cart=cart)
    item.delete()
    messages.success(request, 'Item removed from your cart.')
    return redirect('orders:cart_detail')


@login_required
@transaction.atomic
def checkout(request):
    cart = _get_or_create_cart(request.user)
    cart_items = list(cart.items.select_related('product').all())

    if not cart_items:
        messages.info(request, 'Your cart is empty. Add products before checking out.')
        return redirect('orders:cart_detail')

    subtotal = sum((item.total for item in cart_items), Decimal('0.00'))
    shipping = Decimal('0.00') if subtotal >= Decimal('25000.00') else Decimal('2500.00')
    tax = (subtotal * Decimal('0.075')).quantize(Decimal('0.01'))
    total = subtotal + shipping + tax

    initial = {}
    if hasattr(request.user, 'profile'):
        profile = request.user.profile
        initial = {
            'shipping_address': profile.address or '',
            'shipping_city': profile.city or '',
            'shipping_state': profile.state or '',
            'shipping_zip': profile.zip_code or '',
            'shipping_country': profile.country or 'Nigeria',
        }

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            order = Order.objects.create(
                order_number=_build_order_number(),
                user=request.user,
                shipping_address=form.cleaned_data['shipping_address'],
                shipping_city=form.cleaned_data['shipping_city'],
                shipping_state=form.cleaned_data['shipping_state'],
                shipping_zip=form.cleaned_data['shipping_zip'],
                shipping_country=form.cleaned_data['shipping_country'],
                notes=form.cleaned_data['notes'],
                subtotal=subtotal,
                shipping_cost=shipping,
                tax=tax,
                total=total,
                status='pending',
                payment_status='pending',
            )

            for item in cart_items:
                unit_price = item.product.discounted_price if item.product.is_on_sale else item.product.price
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    quantity=item.quantity,
                    price=unit_price,
                    total=unit_price * item.quantity,
                )
                item.product.stock_quantity = max(item.product.stock_quantity - item.quantity, 0)
                item.product.save(update_fields=['stock_quantity'])

            cart.items.all().delete()
            messages.success(request, f'Order {order.order_number} created successfully. Payment integration can be added next.')
            return redirect('orders:order_history')
    else:
        form = CheckoutForm(initial=initial)

    context = {
        'form': form,
        'cart_items': cart_items,
        'subtotal': subtotal,
        'shipping': shipping,
        'tax': tax,
        'total': total,
    }
    return render(request, 'orders/checkout.html', context)


@login_required
def order_history(request):
    orders = request.user.orders.prefetch_related('items__product').all()
    return render(request, 'orders/order_history.html', {'orders': orders})