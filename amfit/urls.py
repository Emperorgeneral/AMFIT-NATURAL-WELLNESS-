"""
URL configuration for amfit project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic.base import RedirectView

urlpatterns = [
    path(
        'favicon.ico',
        RedirectView.as_view(url=f"{settings.STATIC_URL}favicon.ico", permanent=True),
    ),
    path(settings.ADMIN_URL, admin.site.urls),
    path('account/', include('users.urls')),
    path('', include('orders.urls')),
    path('', include('products.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
