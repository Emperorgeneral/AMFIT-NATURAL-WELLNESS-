"""Custom admin site with dashboard for AMFIT."""

from django.contrib import admin
from django.urls import path
from django.shortcuts import render
from django.db.models import Sum, Count, Q
from django.utils.html import format_html
from orders.models import Order, OrderItem
from products.models import Product, Category
from django.contrib.auth.models import User


class AMFITAdminSite(admin.AdminSite):
    """Custom admin site for AMFIT with enhanced branding and dashboard."""
    
    site_header = "AMFIT Admin Dashboard"
    site_title = "AMFIT Natural Wellness"
    index_title = "Welcome to Your Store Dashboard"
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('dashboard/', self.admin_view(self.dashboard_view), name='admin_dashboard'),
        ]
        return custom_urls + urls
    
    def dashboard_view(self, request):
        """Main dashboard showing key metrics and recent activity."""
        
        # Calculate metrics
        total_orders = Order.objects.count()
        pending_orders = Order.objects.filter(status__in=['pending', 'processing']).count()
        delivered_orders = Order.objects.filter(status='delivered').count()
        total_revenue = Order.objects.filter(status='delivered').aggregate(Sum('total'))['total__sum'] or 0
        
        total_users = User.objects.count()
        total_products = Product.objects.count()
        low_stock = Product.objects.filter(stock_quantity__lt=5).count()
        
        # Recent orders
        recent_orders = Order.objects.select_related('user').order_by('-created_at')[:5]
        
        # Top products (by quantity sold)
        top_products = OrderItem.objects.values('product__name').annotate(
            total_qty=Sum('quantity')
        ).order_by('-total_qty')[:5]
        
        # Order status breakdown
        status_breakdown = Order.objects.values('status').annotate(count=Count('id'))
        
        context = {
            'title': 'Dashboard',
            'total_orders': total_orders,
            'pending_orders': pending_orders,
            'delivered_orders': delivered_orders,
            'total_revenue': f"₦{total_revenue:,.2f}",
            'total_users': total_users,
            'total_products': total_products,
            'low_stock': low_stock,
            'recent_orders': recent_orders,
            'top_products': top_products,
            'status_breakdown': status_breakdown,
        }

        # Include default admin context so sidebar/app navigation remains available.
        context.update(self.each_context(request))
        
        return render(request, 'admin/dashboard.html', context)
    
    def index(self, request, extra_context=None):
        """Override index to redirect to dashboard."""
        return self.dashboard_view(request)


# Create custom admin site instance
amfit_admin_site = AMFITAdminSite(name='amfit_admin')
