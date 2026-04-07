from decimal import Decimal, InvalidOperation
import hashlib
import hmac
import json
import logging
import re
from random import randint
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.validators import validate_email
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


def _build_paystack_reference(order):
    while True:
        timestamp = timezone.now().strftime('%y%m%d%H%M%S%f')
        candidate = f"AMF{order.id}{timestamp}{randint(1000, 9999)}"
        if not Order.objects.filter(paystack_reference=candidate).exists():
            return candidate


def _initialize_paystack_with_retry(order, user, callback_url, max_attempts=3):
    last_message = 'Unable to initialize payment.'
    last_details = {}

    for attempt in range(1, max_attempts + 1):
        result = _paystack_initialize(order, user, callback_url)

        if not result['ok']:
            message = result.get('message', 'Unable to initialize payment.')
            last_message = message
            last_details = result.get('details', {})
            if _is_reference_issue(message) and attempt < max_attempts:
                old_reference = order.paystack_reference
                order.paystack_reference = _build_paystack_reference(order)
                order.save(update_fields=['paystack_reference', 'updated_at'])
                logger.warning(
                    'Retrying Paystack initialize after HTTP reference issue (attempt %s/%s). old=%s new=%s user=%s message=%s',
                    attempt,
                    max_attempts,
                    old_reference,
                    order.paystack_reference,
                    user.id,
                    message,
                )
                continue
            return {'ok': False, 'message': message, 'details': last_details}

        response_data = result['data']
        if response_data.get('status'):
            return {'ok': True, 'data': response_data}

        message = response_data.get('message', 'Unable to initialize payment.')
        last_message = message
        if _is_reference_issue(message) and attempt < max_attempts:
            old_reference = order.paystack_reference
            order.paystack_reference = _build_paystack_reference(order)
            order.save(update_fields=['paystack_reference', 'updated_at'])
            logger.warning(
                'Retrying Paystack initialize after response reference issue (attempt %s/%s). old=%s new=%s user=%s',
                attempt,
                max_attempts,
                old_reference,
                order.paystack_reference,
                user.id,
            )
            continue

        return {'ok': False, 'message': message, 'details': last_details}

    return {'ok': False, 'message': last_message, 'details': last_details}


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
    email = (user.email or '').strip()
    amount_kobo = int((order.total * Decimal('100')).quantize(Decimal('1')))
    reference = (order.paystack_reference or order.order_number or '').strip()

    valid, validation_message = _validate_paystack_initialize_input(
        order=order,
        email=email,
        amount_kobo=amount_kobo,
        reference=reference,
    )
    if not valid:
        logger.error(
            'Paystack initialize validation failed for order=%s user=%s: %s',
            order.order_number,
            user.id,
            validation_message,
        )
        return {'ok': False, 'message': validation_message}

    payload = {
        'email': email,
        'amount': amount_kobo,
        'reference': reference,
        'callback_url': callback_url,
        'metadata': {
            'order_number': order.order_number,
            'paystack_reference': reference,
            'user_id': user.id,
        },
    }

    return _paystack_request('/transaction/initialize', method='POST', payload=payload)


def _paystack_request(path, method='GET', payload=None):
    secret_key = (settings.PAYSTACK_SECRET_KEY or '').strip()
    if not secret_key:
        return {'ok': False, 'message': 'Payment gateway secret key is missing.'}
    if not (secret_key.startswith('sk_test_') or secret_key.startswith('sk_live_')):
        return {'ok': False, 'message': 'Payment gateway secret key format is invalid.'}

    url = f'https://api.paystack.co{path}'
    headers = {
        'Authorization': f'Bearer {secret_key}',
        'Content-Type': 'application/json',
    }

    if not headers.get('Authorization', '').startswith('Bearer '):
        return {'ok': False, 'message': 'Payment request authorization header is invalid.'}
    if headers.get('Content-Type') != 'application/json':
        return {'ok': False, 'message': 'Payment request content-type header is invalid.'}

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
        response_headers = dict(exc.headers.items()) if getattr(exc, 'headers', None) else {}
        try:
            parsed = json.loads(raw) if raw else {}
            message = parsed.get('message') or str(exc)
        except json.JSONDecodeError:
            parsed = {}
            message = raw or str(exc)

        details = {
            'status_code': getattr(exc, 'code', None),
            'reason': str(getattr(exc, 'reason', '')),
            'method': method,
            'path': path,
            'url': url,
            'response_headers': response_headers,
            'response_body': raw,
            'parsed_response': parsed,
        }
        logger.error('Paystack API HTTP error details: %s', json.dumps(details, default=str))
        return {'ok': False, 'message': message, 'details': details}
    except (URLError, TimeoutError) as exc:
        details = {
            'method': method,
            'path': path,
            'url': url,
            'error': str(exc),
        }
        logger.error('Paystack API network error details: %s', json.dumps(details, default=str))
        return {'ok': False, 'message': str(exc), 'details': details}


def _validate_paystack_initialize_input(order, email, amount_kobo, reference):
    if not email:
        return False, 'A valid customer email is required for payment.'

    try:
        validate_email(email)
    except ValidationError:
        return False, 'Customer email format is invalid for payment initialization.'

    if not isinstance(amount_kobo, int) or amount_kobo <= 0:
        return False, 'Payment amount is invalid. Amount must be in kobo and greater than zero.'

    if not reference:
        return False, 'Payment reference is missing.'
    if not re.fullmatch(r'[A-Za-z0-9_-]{6,80}', reference):
        return False, 'Payment reference format is invalid.'

    duplicate_reference = Order.objects.filter(paystack_reference=reference).exclude(id=order.id).exists()
    if duplicate_reference:
        return False, 'Payment reference must be unique.'

    return True, ''


def _resolve_order_by_reference(reference):
    order = Order.objects.filter(paystack_reference=reference).first()
    if order is None:
        order = Order.objects.filter(order_number=reference).first()
    return order


def _mark_order_paid(order):
    if order.payment_status != 'paid':
        order.payment_status = 'paid'
        if order.status == 'pending':
            order.status = 'processing'
        order.save(update_fields=['payment_status', 'status', 'updated_at'])


def _mark_order_payment_failed(order, failed_status='failed'):
    order.payment_status = failed_status
    order.save(update_fields=['payment_status', 'updated_at'])


def _is_reference_issue(message):
    text = (message or '').lower()
    return 'reference' in text or 'duplicate' in text or '1010' in text


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
            order.paystack_reference = _build_paystack_reference(order)
            order.save(update_fields=['paystack_reference', 'updated_at'])

            for item in cart_items:
                unit_price = _get_cart_item_unit_price(item)
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    quantity=item.quantity,
                    price=unit_price,
                    total=unit_price * item.quantity,
                )

            callback_url = request.build_absolute_uri(reverse('orders:payment_verify'))
            result = _initialize_paystack_with_retry(order, request.user, callback_url, max_attempts=3)
            if not result['ok']:
                _mark_order_payment_failed(order, failed_status='failed')
                logger.error(
                    'Checkout payment initialize failed for order %s (user=%s): %s details=%s',
                    order.order_number,
                    request.user.id,
                    result['message'],
                    json.dumps(result.get('details', {}), default=str),
                )
                messages.error(request, f"Unable to initialize payment: {result['message']}")
                return redirect('orders:order_history')

            auth_url = result['data'].get('data', {}).get('authorization_url')
            if not auth_url:
                _mark_order_payment_failed(order, failed_status='failed')
                logger.error('Checkout initialize missing authorization_url for order %s', order.order_number)
                messages.error(request, 'Payment link was not returned by Paystack.')
                return redirect('orders:order_history')

            cart.items.all().delete()
            return redirect(auth_url)
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

    if order.payment_status == 'paid':
        messages.info(request, 'This order is already paid.')
        return redirect('orders:order_history')

    callback_url = request.build_absolute_uri(reverse('orders:payment_verify'))

    # Always rotate the reference before each new initialize attempt to avoid Paystack duplicate reference conflicts.
    order.paystack_reference = _build_paystack_reference(order)
    order.save(update_fields=['paystack_reference', 'updated_at'])

    result = _initialize_paystack_with_retry(order, request.user, callback_url, max_attempts=3)
    if not result['ok']:
        logger.error(
            'Paystack initialize failed after retries for order %s (user=%s): %s details=%s',
            order.paystack_reference,
            request.user.id,
            result['message'],
            json.dumps(result.get('details', {}), default=str),
        )
        messages.error(request, f"Unable to initialize payment: {result['message']}")
        return redirect('orders:order_history')

    response_data = result['data']

    auth_url = response_data.get('data', {}).get('authorization_url')
    if not auth_url:
        logger.error(
            'Paystack initialize missing authorization_url for order %s (user=%s): %s',
            order.paystack_reference,
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

    order = _resolve_order_by_reference(reference)
    if order is None:
        return HttpResponseBadRequest('Unknown payment reference.')
    result = _paystack_request(f'/transaction/verify/{reference}')

    context = {
        'order': order,
        'payment_success': False,
        'payment_state': 'failed',
        'message': 'Payment verification failed.',
        'retry_url': reverse('orders:paystack_initialize', kwargs={'order_number': order.order_number}),
    }

    if not result['ok']:
        _mark_order_payment_failed(order, failed_status='failed')
        context['message'] = f"Payment verification failed: {result['message']}"
        return render(request, 'orders/payment_result.html', context)

    response_data = result['data']
    gateway_data = response_data.get('data', {})
    gateway_status = (gateway_data.get('status') or '').lower()
    expected_amount_kobo = int((order.total * Decimal('100')).quantize(Decimal('1')))
    amount_matches = gateway_data.get('amount') == expected_amount_kobo

    if response_data.get('status') and gateway_status == 'success' and amount_matches:
        _mark_order_paid(order)
        context['payment_success'] = True
        context['payment_state'] = 'paid'
        context['message'] = f'Payment received for order {order.order_number}.'
        context['retry_url'] = ''
        return render(request, 'orders/payment_result.html', context)

    if gateway_status == 'abandoned':
        _mark_order_payment_failed(order, failed_status='abandoned')
        context['payment_state'] = 'abandoned'
        context['message'] = 'Payment session was abandoned. You can retry payment below.'
        return render(request, 'orders/payment_result.html', context)

    _mark_order_payment_failed(order, failed_status='failed')
    if response_data.get('status') and gateway_status == 'success' and not amount_matches:
        context['message'] = 'Payment amount mismatch detected. Please contact support with your order number.'
    else:
        context['message'] = 'Payment was not successful. Please retry payment.'

    return render(request, 'orders/payment_result.html', context)


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
            order = _resolve_order_by_reference(reference)
            if order is not None:
                expected_amount_kobo = int((order.total * Decimal('100')).quantize(Decimal('1')))
                webhook_amount = data.get('amount')
                if webhook_amount == expected_amount_kobo:
                    _mark_order_paid(order)

    return JsonResponse({'status': 'ok'})