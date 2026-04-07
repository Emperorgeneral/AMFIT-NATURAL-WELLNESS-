from decimal import Decimal, InvalidOperation
import hashlib
import hmac
import json
import logging
from random import randint
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from products.models import Product

from .forms import CheckoutForm
from .models import Cart, CartItem, Order, OrderItem


logger = logging.getLogger(__name__)


def _get_or_create_cart(user):
    cart, _ = Cart.objects.get_or_create(user=user)
    return cart


def _build_order_number():
    # Keep generating until we get a unique reference accepted by the DB and Paystack.
    # Keep reference <= 20 chars to match Order.order_number max_length.
    while True:
        timestamp = timezone.now().strftime('%y%m%d%H%M%S')
        candidate = f'AMF{timestamp}{randint(100, 999)}'
        if not Order.objects.filter(order_number=candidate).exists():
            return candidate


def _get_cart_item_unit_price(item):
    try:
        if item.product.is_on_sale and item.product.discounted_price is not None:
            return Decimal(item.product.discounted_price)
        if item.product.price is not None:
            return Decimal(item.product.price)
    except (TypeError, ValueError, InvalidOperation):
        pass

    logger.warning('Invalid product price for product_id=%s in cart_item_id=%s', item.product_id, item.id)
    return Decimal('0.00')


def _get_cart_item_total(item):
    return _get_cart_item_unit_price(item) * item.quantity


def _paystack_initialize(order, user, callback_url):
    email = user.email or f'{user.username}@example.com'
    amount_kobo = int((order.total * Decimal('100')).quantize(Decimal('1')))

    payload = {
        'email': email,
        'amount': amount_kobo,
        'reference': order.order_number,
        'callback_url': callback_url,
        'metadata': {
            'order_number': order.order_number,
            'user_id': user.id,
        },
    }

    return _paystack_request('/transaction/initialize', method='POST', payload=payload)


def _paystack_request(path, method='GET', payload=None):
    if not settings.PAYSTACK_SECRET_KEY:
        return {'ok': False, 'message': 'Payment gateway is not configured yet.'}

    url = f'https://api.paystack.co{path}'
    headers = {
        'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}',
        'Content-Type': 'application/json',
    }

    body = None
    if payload is not None:
        body = json.dumps(payload).encode('utf-8')

    request = Request(url, data=body, headers=headers, method=method)

    try:
        with urlopen(request, timeout=25) as response:
            data = json.loads(response.read().decode('utf-8'))
            return {'ok': True, 'data': data}
    except HTTPError as exc:
        raw = exc.read().decode('utf-8', errors='ignore') if hasattr(exc, 'read') else ''
        try:
            parsed = json.loads(raw) if raw else {}
            message = parsed.get('message') or str(exc)
        except json.JSONDecodeError:
            message = raw or str(exc)
        return {'ok': False, 'message': message}
    except (URLError, TimeoutError) as exc:
        return {'ok': False, 'message': str(exc)}


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
    subtotal = sum((_get_cart_item_total(item) for item in cart_items), Decimal('0.00'))
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

    subtotal = sum((_get_cart_item_total(item) for item in cart_items), Decimal('0.00'))
    shipping = Decimal('0.00') if subtotal >= Decimal('25000.00') else Decimal('2500.00')
    tax = (subtotal * Decimal('0.075')).quantize(Decimal('0.01'))
    total = subtotal + shipping + tax

    initial = {}
    try:
        profile = request.user.profile
    except ObjectDoesNotExist:
        profile = None

    if profile:
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
                unit_price = _get_cart_item_unit_price(item)
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    quantity=item.quantity,
                    price=unit_price,
                    total=unit_price * item.quantity,
                )
                current_stock = item.product.stock_quantity or 0
                item.product.stock_quantity = max(current_stock - item.quantity, 0)
                item.product.save(update_fields=['stock_quantity'])

            cart.items.all().delete()
            messages.success(request, f'Order {order.order_number} created. Continue to Paystack payment.')
            return redirect('orders:paystack_initialize', order_number=order.order_number)
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


@login_required
def paystack_initialize(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)

    if order.payment_status == 'completed':
        messages.info(request, 'This order is already paid.')
        return redirect('orders:order_history')

    callback_url = request.build_absolute_uri(reverse('orders:paystack_callback'))

    result = _paystack_initialize(order, request.user, callback_url)
    if not result['ok']:
        logger.error(
            'Paystack initialize failed for order %s (user=%s): %s',
            order.order_number,
            request.user.id,
            result['message'],
        )
        messages.error(request, f"Unable to initialize payment: {result['message']}")
        return redirect('orders:order_history')

    response_data = result['data']
    if not response_data.get('status'):
        message = response_data.get('message', 'Unable to initialize payment.')
        # Paystack can reject a reused reference (often surfaced as 1010/duplicate).
        if 'reference' in message.lower() or 'duplicate' in message.lower() or '1010' in message:
            old_reference = order.order_number
            order.order_number = _build_order_number()
            order.save(update_fields=['order_number', 'updated_at'])
            logger.warning(
                'Retrying Paystack initialize after reference issue. old=%s new=%s user=%s',
                old_reference,
                order.order_number,
                request.user.id,
            )
            retry = _paystack_initialize(order, request.user, callback_url)
            if not retry['ok']:
                logger.error(
                    'Paystack initialize retry failed for order %s (user=%s): %s',
                    order.order_number,
                    request.user.id,
                    retry['message'],
                )
                messages.error(request, f"Unable to initialize payment: {retry['message']}")
                return redirect('orders:order_history')
            response_data = retry['data']
            if not response_data.get('status'):
                logger.error(
                    'Paystack initialize retry returned non-success for order %s (user=%s): %s',
                    order.order_number,
                    request.user.id,
                    response_data,
                )
                messages.error(request, response_data.get('message', 'Unable to initialize payment.'))
                return redirect('orders:order_history')
        else:
            logger.error(
                'Paystack initialize returned non-success for order %s (user=%s): %s',
                order.order_number,
                request.user.id,
                response_data,
            )
            messages.error(request, message)
            return redirect('orders:order_history')

    auth_url = response_data.get('data', {}).get('authorization_url')
    if not auth_url:
        logger.error(
            'Paystack initialize missing authorization_url for order %s (user=%s): %s',
            order.order_number,
            request.user.id,
            response_data,
        )
        messages.error(request, 'Payment link was not returned by Paystack.')
        return redirect('orders:order_history')

    return redirect(auth_url)


def paystack_callback(request):
    reference = request.GET.get('reference')
    if not reference:
        return HttpResponseBadRequest('Missing payment reference.')

    order = get_object_or_404(Order, order_number=reference)
    result = _paystack_request(f'/transaction/verify/{reference}')

    if not result['ok']:
        order.payment_status = 'failed'
        order.save(update_fields=['payment_status', 'updated_at'])
        messages.error(request, f"Payment verification failed: {result['message']}")
        return redirect('orders:order_history')

    response_data = result['data']
    gateway_data = response_data.get('data', {})
    paid = response_data.get('status') and gateway_data.get('status') == 'success'

    if paid:
        order.payment_status = 'completed'
        order.status = 'processing'
        order.save(update_fields=['payment_status', 'status', 'updated_at'])
        messages.success(request, f'Payment received for order {order.order_number}.')
    else:
        order.payment_status = 'failed'
        order.save(update_fields=['payment_status', 'updated_at'])
        messages.error(request, 'Payment was not successful. Please try again.')

    return redirect('orders:order_history')


@csrf_exempt
@require_POST
def paystack_webhook(request):
    secret = settings.PAYSTACK_WEBHOOK_SECRET or settings.PAYSTACK_SECRET_KEY
    signature = request.headers.get('x-paystack-signature', '')

    if not secret:
        return JsonResponse({'status': 'ignored', 'reason': 'missing secret'}, status=200)

    computed = hmac.new(secret.encode('utf-8'), request.body, hashlib.sha512).hexdigest()
    if not hmac.compare_digest(computed, signature):
        return JsonResponse({'status': 'invalid signature'}, status=401)

    try:
        payload = json.loads(request.body.decode('utf-8'))
    except json.JSONDecodeError:
        return JsonResponse({'status': 'invalid payload'}, status=400)

    if payload.get('event') == 'charge.success':
        data = payload.get('data', {})
        reference = data.get('reference')
        if reference:
            try:
                order = Order.objects.get(order_number=reference)
                order.payment_status = 'completed'
                if order.status == 'pending':
                    order.status = 'processing'
                order.save(update_fields=['payment_status', 'status', 'updated_at'])
            except Order.DoesNotExist:
                pass

    return JsonResponse({'status': 'ok'})