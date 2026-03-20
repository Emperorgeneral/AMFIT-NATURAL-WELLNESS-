from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Subcategory, Product, ProductReview


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'created_at']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'description', 'image')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Subcategory)
class SubcategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'slug', 'created_at']
    list_filter = ['category', 'created_at']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name', 'description', 'category__name']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        (None, {
            'fields': ('category', 'name', 'slug', 'description', 'image')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['product_name', 'category', 'colored_status', 'price_display', 'stock_display', 'rating_display', 'created_at']
    list_filter = ['status', 'category', 'subcategory', 'created_at', 'price']
    search_fields = ['name', 'sku', 'description', 'category__name']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at', 'updated_at', 'rating', 'review_count', 'sku_readonly']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'sku', 'description', 'image')
        }),
        ('Categorization', {
            'fields': ('category', 'subcategory')
        }),
        ('Pricing', {
            'fields': ('price', 'discounted_price')
        }),
        ('Inventory', {
            'fields': ('stock_quantity', 'status')
        }),
        ('Ratings & Reviews', {
            'fields': ('rating', 'review_count'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def product_name(self, obj):
        return f"{obj.name[:50]}..."
    product_name.short_description = "Product Name"
    
    def colored_status(self, obj):
        colors = {'active': '#00b894', 'inactive': '#d63031', 'discontinued': '#636e72'}
        color = colors.get(obj.status, '#000')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 15px; display: inline-block;">{}</span>',
            color,
            obj.get_status_display()
        )
    colored_status.short_description = "Status"
    
    def price_display(self, obj):
        if obj.discounted_price and obj.discounted_price < obj.price:
            return format_html(
                '<span style="color: red; text-decoration: line-through;">₦{}</span> <strong>₦{}</strong>',
                obj.price, obj.discounted_price
            )
        return f"₦{obj.price}"
    price_display.short_description = "Price"
    
    def stock_display(self, obj):
        if obj.stock_quantity < 5:
            color = '#d63031'
        elif obj.stock_quantity < 20:
            color = '#fdcb6e'
        else:
            color = '#00b894'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} units</span>',
            color, obj.stock_quantity
        )
    stock_display.short_description = "Stock"
    
    def rating_display(self, obj):
        if obj.rating:
            return f"⭐ {obj.rating} ({obj.review_count} reviews)"
        return "No ratings"
    rating_display.short_description = "Rating"
    
    def sku_readonly(self, obj):
        return obj.sku

    def mark_active(self, request, queryset):
        queryset.update(status='active')
    mark_active.short_description = "Mark selected as Active"

    def mark_inactive(self, request, queryset):
        queryset.update(status='inactive')
    mark_inactive.short_description = "Mark selected as Inactive"


@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ['product', 'user', 'rating', 'created_at']
    list_filter = ['rating', 'created_at', 'product']
    search_fields = ['product__name', 'user__username', 'comment']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        (None, {
            'fields': ('product', 'user', 'rating', 'comment')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
