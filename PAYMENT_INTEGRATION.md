# Flutterwave Payment Integration Guide

This guide will help you integrate Flutterwave payment processing into the AMFIT e-commerce platform.

## Prerequisites

1. **Flutterwave Account**: https://flutterwave.com/
2. **API Keys**: Get your public and secret keys from Flutterwave dashboard
3. **Installation**: `pip install flutterwave-python requests`

## Step 1: Get Flutterwave Credentials

1. Sign up at https://flutterwave.com/
2. Navigate to Dashboard → Settings → API Keys
3. Copy:
   - **Public Key** (starts with "FLWR_PUB")
   - **Secret Key** (starts with "FLWR_SK")

## Step 2: Store Credentials in Environment

Update `.env` file:
```
FLUTTERWAVE_PUBLIC_KEY=FLWR_PUB_xxxxxxxxxxxx
FLUTTERWAVE_SECRET_KEY=FLWR_SK_xxxxxxxxxxxx
```

Update `amfit/settings.py`:
```python
import os
from decouple import config

FLUTTERWAVE_PUBLIC_KEY = config('FLUTTERWAVE_PUBLIC_KEY')
FLUTTERWAVE_SECRET_KEY = config('FLUTTERWAVE_SECRET_KEY')
FLUTTERWAVE_WEBHOOK_SECRET = config('FLUTTERWAVE_WEBHOOK_SECRET', default='')
```

## Step 3: Create Payment Views

Create `payments/views.py`:

```python
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.conf import settings
from orders.models import Order
import requests
import json
from django.contrib.auth.decorators import login_required

@login_required
def initiate_payment(request):
    """Initialize payment with Flutterwave"""
    if request.method == 'POST':
        # Get order from session or database
        order_id = request.POST.get('order_id')
        order = Order.objects.get(id=order_id, user=request.user)
        
        # Prepare payment payload
        payload = {
            "tx_ref": f"ORDER-{order.order_number}",
            "amount": float(order.total),
            "currency": "NGN",
            "payment_options": "card,mobilemoney,ussd",
            "customer": {
                "email": request.user.email,
                "name": request.user.get_full_name() or request.user.username,
                "phonenumber": getattr(request.user.profile, 'phone', '')
            },
            "customizations": {
                "title": "AMFIT E-Commerce",
                "description": f"Order {order.order_number}",
                "logo": "https://yourdomain.com/logo.png"  # Update with your logo
            },
            "redirect_url": f"{request.build_absolute_uri('/payments/callback')}"
        }
        
        # Call Flutterwave API
        headers = {
            "Authorization": f"Bearer {settings.FLUTTERWAVE_SECRET_KEY}"
        }
        
        response = requests.post(
            "https://api.flutterwave.com/v3/payments",
            headers=headers,
            json=payload
        )
        
        if response.status_code == 200:
            data = response.json()
            return redirect(data['data']['link'])
        else:
            return render(request, 'payments/error.html', {'error': 'Payment initiation failed'})
    
    return render(request, 'payments/initiate_payment.html')


def payment_callback(request):
    """Handle Flutterwave payment callback"""
    transaction_id = request.GET.get('transaction_id')
    
    if not transaction_id:
        return render(request, 'payments/error.html', {'error': 'No transaction ID'})
    
    # Verify payment with Flutterwave
    headers = {
        "Authorization": f"Bearer {settings.FLUTTERWAVE_SECRET_KEY}"
    }
    
    response = requests.get(
        f"https://api.flutterwave.com/v3/transactions/{transaction_id}/verify",
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        status = data['status']
        
        if status == 'success':
            tx_ref = data['data']['tx_ref']
            order_number = tx_ref.replace('ORDER-', '')
            
            try:
                order = Order.objects.get(order_number=order_number)
                order.payment_status = 'completed'
                order.status = 'processing'
                order.save()
                
                # Send confirmation email (implement email sending)
                
                return render(request, 'payments/success.html', {'order': order})
            except Order.DoesNotExist:
                return render(request, 'payments/error.html', {'error': 'Order not found'})
        else:
            return render(request, 'payments/error.html', {'error': 'Payment failed'})
    
    return render(request, 'payments/error.html', {'error': 'Payment verification failed'})


@require_POST
def webhook(request):
    """Handle Flutterwave webhook notifications"""
    try:
        payload = json.loads(request.body)
        
        # Verify webhook secret
        webhook_secret = settings.FLUTTERWAVE_WEBHOOK_SECRET
        if webhook_secret and request.META.get('HTTP_VERIFI_HASH') != webhook_secret:
            return JsonResponse({'status': 'error'}, status=401)
        
        # Process payment notification
        if payload['event'] == 'charge.completed':
            tx_ref = payload['data']['tx_ref']
            order_number = tx_ref.replace('ORDER-', '')
            
            order = Order.objects.get(order_number=order_number)
            order.payment_status = 'completed'
            order.save()
    
    except Exception as e:
        print(f"Webhook error: {e}")
    
    return JsonResponse({'status': 'ok'})
```

## Step 4: Create Payment App

```bash
python manage.py startapp payments
```

Create `payments/urls.py`:

```python
from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('initiate/', views.initiate_payment, name='initiate'),
    path('callback/', views.payment_callback, name='callback'),
    path('webhook/', views.webhook, name='webhook'),
]
```

Add to `amfit/urls.py`:

```python
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('products.urls')),
    path('payments/', include('payments.urls')),
]
```

## Step 5: Create Payment Templates

`templates/payments/initiate_payment.html`:

```html
{% extends 'base.html' %}

{% block title %}Complete Payment - AMFIT{% endblock %}

{% block content %}
<div class="container">
    <div style="max-width: 600px; margin: 2rem auto; background: white; padding: 2rem; border-radius: 8px;">
        <h1 style="margin-bottom: 1rem;">Complete Payment</h1>
        
        <div style="background: #f9f9f9; padding: 1rem; border-radius: 4px; margin-bottom: 2rem;">
            <h3>Order Summary</h3>
            <p><strong>Order Number:</strong> #12345</p>
            <p><strong>Total Amount:</strong> ₦50,000.00</p>
            <p><strong>Status:</strong> Pending Payment</p>
        </div>
        
        <form method="POST">
            {% csrf_token %}
            <input type="hidden" name="order_id" value="{{ order.id }}">
            <button type="submit" class="btn" style="width: 100%; padding: 1rem;">
                Pay with Flutterwave
            </button>
        </form>
    </div>
</div>
{% endblock %}
```

`templates/payments/success.html`:

```html
{% extends 'base.html' %}

{% block title %}Payment Successful - AMFIT{% endblock %}

{% block content %}
<div class="container">
    <div style="max-width: 600px; margin: 2rem auto; background: white; padding: 2rem; border-radius: 8px; text-align: center;">
        <div style="font-size: 48px; color: #27ae60; margin-bottom: 1rem;">✓</div>
        <h1 style="color: #27ae60; margin-bottom: 1rem;">Payment Successful!</h1>
        
        <p style="font-size: 16px; color: #666; margin-bottom: 2rem;">
            Your order has been confirmed and is being processed.
        </p>
        
        <div style="background: #f9f9f9; padding: 1rem; border-radius: 4px; margin-bottom: 2rem; text-align: left;">
            <h3>Order Details</h3>
            <p><strong>Order Number:</strong> {{ order.order_number }}</p>
            <p><strong>Total Amount:</strong> ₦{{ order.total }}</p>
            <p><strong>Status:</strong> {{ order.get_status_display }}</p>
        </div>
        
        <p style="color: #666; margin-bottom: 2rem;">
            A confirmation email has been sent to your email address.
        </p>
        
        <a href="{% url 'products:home' %}" class="btn">Continue Shopping</a>
    </div>
</div>
{% endblock %}
```

`templates/payments/error.html`:

```html
{% extends 'base.html' %}

{% block title %}Payment Error - AMFIT{% endblock %}

{% block content %}
<div class="container">
    <div style="max-width: 600px; margin: 2rem auto; background: white; padding: 2rem; border-radius: 8px; text-align: center;">
        <div style="font-size: 48px; color: #e74c3c; margin-bottom: 1rem;">✗</div>
        <h1 style="color: #e74c3c; margin-bottom: 1rem;">Payment Failed</h1>
        
        <p style="font-size: 16px; color: #666; margin-bottom: 2rem;">
            {{ error }}
        </p>
        
        <a href="{% url 'products:home' %}" class="btn">Back to Home</a>
    </div>
</div>
{% endblock %}
```

## Step 6: Update Order Model

Add to `orders/models.py`:

```python
class Order(models.Model):
    # ... existing fields ...
    flutterwave_ref = models.CharField(max_length=100, blank=True, null=True)
    flutterwave_transaction_id = models.CharField(max_length=100, blank=True, null=True)
```

Run migration:
```bash
python manage.py makemigrations
python manage.py migrate
```

## Step 7: Update Checkout Page

Add payment button in checkout template:

```html
<form method="POST" action="{% url 'payments:initiate' %}">
    {% csrf_token %}
    <input type="hidden" name="order_id" value="{{ order.id }}">
    <button type="submit" class="btn">Proceed to Payment</button>
</form>
```

## Step 8: Test Payment

1. Flutterwave provides test card numbers:
   - Visa: 4239 1100 1234 5678
   - CVV: 981
   - Expiry: Any future date

2. Make payment in development:
   - Visit checkout page
   - Click "Proceed to Payment"
   - You'll be redirected to Flutterwave (test mode)
   - Use test card details
   - Confirm payment
   - You'll be redirected back to success page

## Production Checklist

- [ ] Switch Flutterwave to live API keys
- [ ] Update callback URL to production domain
- [ ] Configure webhook secret
- [ ] Test with real transactions (small amount)
- [ ] Enable email notifications
- [ ] Set up payment receipts
- [ ] Configure order status updates
- [ ] Add transaction logging
- [ ] Monitor payment failures

## Troubleshooting

**Issue: Payment callback not working**
- Check Flutterwave IP is whitelisted
- Verify webhook URL is publicly accessible
- Check webhook secret matches

**Issue: Transaction verification fails**
- Ensure API keys are correct
- Check transaction ID is valid
- Verify order exists in database

**Issue: Customer not receiving confirmation**
- Configure email backend in settings
- Add email service (Gmail, SendGrid, etc.)
- Test email sending separately

## Security Notes

1. **Never expose secret keys** in frontend/client code
2. **Always verify** payments on backend with Flutterwave
3. **Use HTTPS** in production
4. **Validate amounts** before processing
5. **Log all transactions** for audit trail
6. **Handle webhook timeouts** gracefully

## Resources

- Flutterwave API Docs: https://developer.flutterwave.com/
- Flutterwave Python SDK: https://github.com/Flutterwave/Flutterwave-Django-v3
- Django Payments: https://github.com/jazzband/django-payments

## Support

For issues contact:
- Flutterwave Support: https://support.flutterwave.com
- Django Community: https://www.djangoproject.com/
