from django.shortcuts import render, get_object_or_404
from django.db.models import Avg, Q
from django.core.paginator import Paginator
from .models import Product, Category, Subcategory, ProductReview


def home(request):
    """Home page with featured products"""
    featured_products = Product.objects.filter(status='active')[:8]
    categories = Category.objects.all()
    context = {
        'featured_products': featured_products,
        'categories': categories,
    }
    return render(request, 'products/home.html', context)


def category_list(request):
    """Display all categories"""
    categories = Category.objects.all()
    context = {
        'categories': categories,
    }
    return render(request, 'products/category_list.html', context)


def category_detail(request, slug):
    """Display products by category"""
    category = get_object_or_404(Category, slug=slug)
    subcategories = category.subcategories.all()
    products = category.products.filter(status='active')
    
    # Filtering and Search
    search_query = request.GET.get('search', '')
    price_min = request.GET.get('price_min')
    price_max = request.GET.get('price_max')
    sort_by = request.GET.get('sort', '-created_at')
    
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) | Q(description__icontains=search_query)
        )
    
    if price_min:
        products = products.filter(price__gte=float(price_min))
    if price_max:
        products = products.filter(price__lte=float(price_max))
    
    products = products.order_by(sort_by)
    
    # Pagination
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'category': category,
        'subcategories': subcategories,
        'page_obj': page_obj,
        'products': page_obj.object_list,
        'search_query': search_query,
        'sort_by': sort_by,
        'price_min': price_min,
        'price_max': price_max,
    }
    return render(request, 'products/category_detail.html', context)


def subcategory_detail(request, category_slug, subcategory_slug):
    """Display products by subcategory"""
    category = get_object_or_404(Category, slug=category_slug)
    subcategory = get_object_or_404(Subcategory, category=category, slug=subcategory_slug)
    products = subcategory.products.filter(status='active')
    
    # Filtering and Search
    search_query = request.GET.get('search', '')
    price_min = request.GET.get('price_min')
    price_max = request.GET.get('price_max')
    sort_by = request.GET.get('sort', '-created_at')
    
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) | Q(description__icontains=search_query)
        )
    
    if price_min:
        products = products.filter(price__gte=float(price_min))
    if price_max:
        products = products.filter(price__lte=float(price_max))
    
    products = products.order_by(sort_by)
    
    # Pagination
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'category': category,
        'subcategory': subcategory,
        'page_obj': page_obj,
        'products': page_obj.object_list,
        'search_query': search_query,
        'sort_by': sort_by,
        'price_min': price_min,
        'price_max': price_max,
    }
    return render(request, 'products/subcategory_detail.html', context)


def product_detail(request, slug):
    """Display single product with details and reviews"""
    product = get_object_or_404(Product, slug=slug, status='active')
    reviews = product.reviews.all().order_by('-created_at')
    related_products = Product.objects.filter(
        subcategory=product.subcategory,
        status='active'
    ).exclude(id=product.id)[:4]
    
    # Calculate average rating
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
    
    context = {
        'product': product,
        'reviews': reviews,
        'related_products': related_products,
        'avg_rating': avg_rating,
    }
    return render(request, 'products/product_detail.html', context)


def search_products(request):
    """Search for products across all categories"""
    query = request.GET.get('q', '')
    sort_by = request.GET.get('sort', '-created_at')
    products = Product.objects.filter(status='active')
    
    if query:
        products = products.filter(
            Q(name__icontains=query) | 
            Q(description__icontains=query) |
            Q(category__name__icontains=query) |
            Q(subcategory__name__icontains=query)
        )

    products = products.order_by(sort_by)
    
    # Pagination
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'query': query,
        'page_obj': page_obj,
        'products': page_obj.object_list,
        'sort_by': sort_by,
    }
    return render(request, 'products/search_results.html', context)
