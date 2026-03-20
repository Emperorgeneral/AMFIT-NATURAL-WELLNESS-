"""
URL configuration for amfit project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic.base import RedirectView
from amfit.admin_site import amfit_admin_site

# Register all models with custom admin site
from products.admin import CategoryAdmin, SubcategoryAdmin, ProductAdmin, ProductReviewAdmin
from orders.admin import OrderAdmin, OrderItemAdmin, CartAdmin, CartItemAdmin
from users.admin import UserProfileAdmin, VerificationTokenAdmin
from products.models import Category, Subcategory, Product, ProductReview
from orders.models import Order, OrderItem, Cart, CartItem
from users.models import UserProfile, VerificationToken
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

# Register models with custom admin site
amfit_admin_site.register(Category, CategoryAdmin)
amfit_admin_site.register(Subcategory, SubcategoryAdmin)
amfit_admin_site.register(Product, ProductAdmin)
amfit_admin_site.register(ProductReview, ProductReviewAdmin)
amfit_admin_site.register(Order, OrderAdmin)
amfit_admin_site.register(OrderItem, OrderItemAdmin)
amfit_admin_site.register(Cart, CartAdmin)
amfit_admin_site.register(CartItem, CartItemAdmin)
amfit_admin_site.register(UserProfile, UserProfileAdmin)
amfit_admin_site.register(VerificationToken, VerificationTokenAdmin)
amfit_admin_site.register(User, DjangoUserAdmin)

urlpatterns = [
    path(
        'favicon.ico',
        RedirectView.as_view(url=f"{settings.STATIC_URL}favicon.ico", permanent=True),
    ),
    path(settings.ADMIN_URL, amfit_admin_site.urls),
    path('account/', include('users.urls')),
    path('', include('orders.urls')),
    path('', include('products.urls')),
]

# Uploaded media must be reachable in production as well.
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
