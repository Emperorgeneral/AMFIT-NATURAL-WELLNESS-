import logging

from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse


logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware:
    """Attach defensive HTTP headers to every response."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Only set headers when upstream did not already define them.
        response.setdefault('X-Content-Type-Options', 'nosniff')
        response.setdefault('Referrer-Policy', getattr(settings, 'SECURE_REFERRER_POLICY', 'strict-origin-when-cross-origin'))
        response.setdefault('Permissions-Policy', getattr(settings, 'PERMISSIONS_POLICY', 'camera=(), microphone=(), geolocation=()'))
        response.setdefault('Cross-Origin-Resource-Policy', getattr(settings, 'SECURE_CROSS_ORIGIN_RESOURCE_POLICY', 'same-site'))

        csp = getattr(settings, 'CONTENT_SECURITY_POLICY', '')
        if csp:
            response.setdefault('Content-Security-Policy', csp)

        return response


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
                logger.warning(
                    'Rate limit hit for ip=%s path=%s method=%s rule=%s',
                    client_ip,
                    path,
                    method,
                    index,
                )
                response = HttpResponse(
                    'Too many requests. Please wait a moment and try again.',
                    status=429,
                )
                response['Retry-After'] = str(rule['window'])
                return response

            try:
                cache.incr(key)
            except ValueError:
                cache.set(key, count + 1, timeout=rule['window'])
            break

        return self.get_response(request)

    @staticmethod
    def _get_client_ip(request):
        remote_addr = (request.META.get('REMOTE_ADDR') or '').strip()
        trusted_proxies = set(getattr(settings, 'RATE_LIMIT_TRUSTED_PROXIES', []))

        # Only trust forwarding headers when the request came from an explicit proxy.
        if remote_addr and remote_addr in trusted_proxies:
            cf_ip = request.META.get('HTTP_CF_CONNECTING_IP')
            if cf_ip:
                return cf_ip.strip()

            forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR', '')
            if forwarded_for:
                return forwarded_for.split(',')[0].strip()

        if remote_addr:
            return remote_addr

        return 'unknown'