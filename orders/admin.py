from django.contrib import admin
from django.utils.html import format_html
from .models import Order, OrderItem, Cart, CartItem


class OrderItemInline(admin.TabularInline):
    """Inline admin for order items"""
    model = OrderItem
    extra = 0
    fields = ['product', 'quantity', 'price', 'total']
    readonly_fields = ['total']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'customer_email', 'colored_status', 'payment_status_color', 'total_display', 'created_at']
    list_filter = ['status', 'payment_status', 'created_at', 'total']
    search_fields = ['order_number', 'user__username', 'user__email', 'shipping_address']
    readonly_fields = ['order_number', 'created_at', 'updated_at', 'subtotal', 'total']
    inlines = [OrderItemInline]
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    fieldsets = (
        ('Order Information', {
            'fields': ('order_number', 'user', 'status', 'payment_status', 'tracking_number')
        }),
        ('Shipping Address', {
            'fields': ('shipping_address', 'shipping_city', 'shipping_state', 'shipping_zip', 'shipping_country')
        }),
        ('Pricing', {
            'fields': ('subtotal', 'shipping_cost', 'tax', 'total')
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def customer_email(self, obj):
        return obj.user.email
    customer_email.short_description = "Customer"
    
    def colored_status(self, obj):
        colors = {
            'pending': '#fdcb6e',
            'processing': '#74b9ff',
            'shipped': '#a29bfe',
            'delivered': '#00b894',
            'cancelled': '#d63031'
        }
        color = colors.get(obj.status, '#636e72')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 12px; border-radius: 20px; display: inline-block;">{}</span>',
            color,
            obj.get_status_display()
        )
    colored_status.short_description = "Order Status"
    
    def payment_status_color(self, obj):
        colors = {
            'pending': '#fdcb6e',
            'paid': '#00b894',
            'failed': '#d63031'
        }
        color = colors.get(obj.payment_status, '#636e72')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 12px; border-radius: 20px; display: inline-block;">{}</span>',
            color,
            obj.get_payment_status_display()
        )
    payment_status_color.short_description = "Payment"
    
    def total_display(self, obj):
        return format_html('<strong>₦{:,.2f}</strong>', obj.total)
    total_display.short_description = "Total"

    def mark_processing(self, request, queryset):
        queryset.update(status='processing')
    mark_processing.short_description = "📦 Mark as Processing"

    def mark_shipped(self, request, queryset):
        queryset.update(status='shipped')
    mark_shipped.short_description = "🚚 Mark as Shipped"

    def mark_delivered(self, request, queryset):
        queryset.update(status='delivered')
    mark_delivered.short_description = "✅ Mark as D
        queryset.update(status='delivered')
    mark_delivered.short_description = "Mark as delivered"


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'product', 'quantity', 'price', 'total']
    list_filter = ['order__created_at']
    search_fields = ['order__order_number', 'product__name']
    readonly_fields = ['total']


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['user', 'created_at', 'updated_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ['cart', 'product', 'quantity', 'total']
    list_filter = ['added_at']
    search_fields = ['cart__user__username', 'product__name']
