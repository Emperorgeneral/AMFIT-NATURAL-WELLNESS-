from django.core.cache import cache
from django.http import HttpResponse


class SimpleRateLimitMiddleware:
    """Basic IP-based throttling for sensitive routes."""

    RULES = [
        {
            'prefixes': ('/admin/', '/account/login/', '/account/signup/'),
            'methods': {'POST'},
            'limit': 10,
            'window': 600,
        },
        {
            'prefixes': ('/cart/', '/checkout/', '/orders/history/'),
            'methods': {'POST'},
            'limit': 40,
            'window': 300,
        },
        {
            'prefixes': ('/search/',),
            'methods': {'GET'},
            'limit': 120,
            'window': 60,
        },
        {
            'prefixes': ('/',),
            'methods': {'GET', 'POST'},
            'limit': 600,
            'window': 60,
        },
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        client_ip = self._get_client_ip(request)
        path = request.path
        method = request.method.upper()

        for index, rule in enumerate(self.RULES):
            if method not in rule['methods']:
                continue
            if not any(path.startswith(prefix) for prefix in rule['prefixes']):
                continue

            key = f"amfit:ratelimit:{index}:{client_ip}"
            count = cache.get(key)
            if count is None:
                cache.set(key, 1, timeout=rule['window'])
                break

            if count >= rule['limit']:
                return HttpResponse(
                    'Too many requests. Please wait a moment and try again.',
                    status=429,
                )

            try:
                cache.incr(key)
            except ValueError:
                cache.set(key, count + 1, timeout=rule['window'])
            break

        return self.get_response(request)

    @staticmethod
    def _get_client_ip(request):
        cf_ip = request.META.get('HTTP_CF_CONNECTING_IP')
        if cf_ip:
            return cf_ip.strip()

        forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR', '')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()

        return request.META.get('REMOTE_ADDR', 'unknown')