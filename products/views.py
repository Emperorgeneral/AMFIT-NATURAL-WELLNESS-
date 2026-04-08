from django.shortcuts import render, get_object_or_404
from django.db.models import Avg, Q, Sum
from django.db.utils import OperationalError, ProgrammingError
from django.core.paginator import Paginator
from .models import Product, Category, Subcategory, ProductReview


def _db_ready():
    """Return False when migrations have not been applied yet in production."""
    try:
        Category.objects.exists()
        Product.objects.exists()
        return True
    except (OperationalError, ProgrammingError):
        return False


def home(request):
    """Home page with featured products"""
    if _db_ready():
        selling_statuses = ['processing', 'ready', 'shipped', 'delivered']

        top_sellers = (
            Product.objects.filter(status='active')
            .annotate(
                total_ordered=Sum(
                    'orderitem__quantity',
                    filter=Q(orderitem__order__status__in=selling_statuses),
                )
            )
            .order_by('-total_ordered', '-created_at')
        )

        # Fallback to newest active products when there are no order stats yet.
        if not top_sellers.exclude(total_ordered__isnull=True).exists():
            top_sellers = Product.objects.filter(status='active').order_by('-created_at')

        categories = (
            Category.objects.filter(products__status='active')
            .distinct()
            .order_by('name')
        )

        category_sections = []
        for category in categories:
            section_products = (
                Product.objects.filter(category=category, status='active')
                .order_by('-created_at')[:10]
            )
            if section_products:
                category_sections.append(
                    {
                        'category': category,
                        'products': section_products,
                    }
                )
    else:
        top_sellers = Product.objects.none()
        category_sections = []

    context = {
        'top_sellers': top_sellers[:10],
        'category_sections': category_sections,
    }
    return render(request, 'products/home.html', context)


def category_list(request):
    """Display all categories"""
    if _db_ready():
        categories = Category.objects.all()
    else:
        categories = Category.objects.none()
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

    if not _db_ready():
        context = {
            'query': query,
            'page_obj': Paginator(Product.objects.none(), 12).get_page(1),
            'products': Product.objects.none(),
            'sort_by': sort_by,
        }
        return render(request, 'products/search_results.html', context)

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


def about_us(request):
    """About Us page"""
    return render(request, 'pages/about_us.html')


def contact(request):
    """Contact Us page"""
    return render(request, 'pages/contact.html')


def privacy_policy(request):
    """Privacy Policy page"""
    return render(request, 'pages/privacy_policy.html')


def terms_conditions(request):
    """Terms and Conditions page"""
    return render(request, 'pages/terms_conditions.html')
