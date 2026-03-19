# AMFIT E-Commerce Setup Guide

## What Has Been Created

Your Django e-commerce backend is now fully scaffolded with:

✅ **Complete Database Models**
- Products, Categories, Subcategories with relationships
- User profiles and authentication setup
- Orders, CartItems, and complete e-commerce data structure

✅ **Admin Dashboard (Django Admin)**
- Full CRUD operations for all products
- Category and subcategory management
- Order tracking and management
- User profile management

✅ **Frontend with Product Browsing**
- Home page with featured products
- Category browsing
- Subcategory filtering
- Search functionality
- Product detail pages with reviews
- Responsive design with embedded CSS

✅ **Backend Infrastructure**
- Views for all product-related pages
- URL routing configured
- Pagination (12 items per page)
- Filtering and sorting

---

## Installation Steps (Windows)

### 1. Open Terminal in Project Directory

```bash
cd "c:\Users\Michael Favour\Downloads\amfit e-commerce\amfit_ecommerce"
```

### 2. Create Virtual Environment

```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Database (PostgreSQL)

**Option A: Use PostgreSQL (Recommended)**

Install PostgreSQL if not already installed:
- Download from https://www.postgresql.org/download/
- During installation, remember the password for `postgres` user
- OpenPgAdmin after installation

Create database:
```bash
# In pgAdmin or psql terminal
CREATE DATABASE amfit_db;
```

Update environment variables in `settings.py` or create `.env`:
```
DB_NAME=amfit_db
DB_USER=postgres
DB_PASSWORD=your_postgres_password
DB_HOST=localhost
DB_PORT=5432
```

**Option B: Use SQLite (Quick Start)**

For quick testing, SQLite is already configured. Skip to step 5.

### 5. Run Migrations

```bash
python manage.py migrate
```

This creates all database tables for products, users, orders, etc.

### 6. Create Admin User (Superuser)

```bash
python manage.py createsuperuser
```

Enter email and password when prompted.

### 7. Start Development Server

```bash
python manage.py runserver
```

Output will show:
```
Starting development server at http://127.0.0.1:8000/
```

### 8. Access the Application

**Frontend:** http://localhost:8000/
- Home page with navigation
- Browse categories
- Search products

**Admin Dashboard:** http://localhost:8000/admin/
- Login with superuser credentials
- Add products, categories, manage orders

---

## Adding Sample Data

### Via Admin Dashboard (Easy)

1. Go to http://localhost:8000/admin/
2. Click **Categories** → **Add Category**
   - Name: `Medical`
   - Slug: `medical`
   - Save
3. Click **Subcategories** → **Add Subcategory**
   - Category: `Medical`
   - Name: `Vitamins`
   - Slug: `vitamins`
   - Save
4. Click **Products** → **Add Product**
   - Name: `Vitamin C 500mg`
   - SKU: `VITC-001`
   - Category: `Medical`
   - Subcategory: `Vitamins`
   - Price: `5000`
   - Stock: `100`
   - Save

Now visit http://localhost:8000/ to see your product!

### Via Python Shell (Advanced)

```bash
python manage.py shell

# In the Python shell:
from products.models import Category, Subcategory, Product

cat = Category.objects.create(
    name="Medical",
    slug="medical",
    description="Medical and health products"
)

sub = Subcategory.objects.create(
    category=cat,
    name="Vitamins",
    slug="vitamins"
)

Product.objects.create(
    name="Vitamin C 500mg",
    description="High-quality vitamin C supplement for immune health",
    price=5000,
    category=cat,
    subcategory=sub,
    slug="vitamin-c-500mg",
    sku="VITC-001",
    stock_quantity=100
)

exit()
```

---

## Project Routes

### Frontend (Public - No Login Required)

| Route | Purpose |
|-------|---------|
| `/` | Home page with featured products |
| `/categories/` | Browse all categories |
| `/category/medical/` | View products in category |
| `/category/medical/subcategory/vitamins/` | View subcategory products |
| `/product/vitamin-c-500mg/` | Single product details page |
| `/search/?q=vitamin` | Search products |

### Admin (Requires Login)

| Route | Purpose |
|-------|---------|
| `/admin/` | Admin login & dashboard |
| `/admin/products/product/` | Manage all products |
| `/admin/products/category/` | Manage categories |
| `/admin/products/subcategory/` | Manage subcategories |
| `/admin/orders/order/` | Manage orders |

---

## Current Features

### ✅ Product Management
- Multiple categories/subcategories
- Product details (name, description, price, image)
- Discount pricing
- Stock management
- Product ratings and reviews

### ✅ Admin Dashboard
- Full CRUD for products
- Category management
- Order tracking
- User profiles
- Review moderation

### ✅ Frontend Features
- Product browsing by category
- Search functionality
- Price filtering
- Sorting (price, popularity, date)
- Pagination
- Responsive design

---

## Next Steps to Complete the Project

### Phase 1: User Authentication (Priority: HIGH)
- [ ] Sign up page
- [ ] Login page
- [ ] Logout functionality
- [ ] Profile management
- [ ] Email verification

**Files to create:**
- `users/views.py` - Auth views
- `users/forms.py` - Auth forms
- `templates/auth/signup.html`
- `templates/auth/login.html`

### Phase 2: Shopping Cart & Checkout (Priority: HIGH)
- [ ] "Add to Cart" button functionality
- [ ] Cart page
- [ ] Cart item management
- [ ] Checkout process
- [ ] Address validation

**Files to create:**
- `orders/views.py` - Cart & checkout logic
- `templates/orders/cart.html`
- `templates/orders/checkout.html`

### Phase 3: Payment Integration (Priority: HIGH)
- [ ] Flutterwave API integration
- [ ] Payment page
- [ ] Payment verification
- [ ] Order confirmation
- [ ] Payment notifications

**Resources:**
- Flutterwave API: https://developer.flutterwave.com/
- Install: `pip install flutterwave-python`

### Phase 4: Additional Features (Priority: MEDIUM)
- [ ] Wishlist
- [ ] Order history
- [ ] Email notifications
- [ ] Product reviews submission
- [ ] Order tracking

### Phase 5: Deployment (Priority: LOW)
- [ ] Set up production database
- [ ] Configure static files
- [ ] Set up email backend
- [ ] Deploy to Heroku/AWS/DigitalOcean
- [ ] Configure SSL/HTTPS

---

## Development Tips

### Add Product Image

1. Go to Admin → Products
2. Edit a product
3. Click "Choose File" for image
4. Upload image (JPG, PNG recommended)
5. Save

Images are stored in `/media/products/` directory.

### Test Views in Python Shell

```bash
python manage.py shell

from products.models import Product
products = Product.objects.all()
print(products)

product = Product.objects.first()
print(f"Product: {product.name}, Price: {product.price}")
```

### Collect Static Files (For Production)

```bash
python manage.py collectstatic
```

### Run Tests

```bash
python manage.py test
```

---

## Troubleshooting

### Issue: Port 8000 already in use
```bash
python manage.py runserver 8001
```

### Issue: Database connection error
- Verify PostgreSQL is running
- Check DB credentials in `amfit/settings.py`
- Reinitialize database: `python manage.py migrate --run-syncdb`

### Issue: Cannot import models
- Ensure migrations are run: `python manage.py migrate`
- Check `INSTALLED_APPS` in `settings.py`

### Issue: Admin page won't load
- Create superuser: `python manage.py createsuperuser`
- Clear cache: `python manage.py clear_cache` (if caching is configured)

---

## Project File Structure Reference

```
amfit_ecommerce/
├── amfit/                          # Django project settings
│   ├── settings.py                # Main configuration
│   ├── urls.py                    # Root URL config
│   ├── wsgi.py / asgi.py          # Server configs
│
├── products/                       # Products app
│   ├── models.py                  # Category, Product, Review models ✅
│   ├── views.py                   # Product listing views ✅
│   ├── urls.py                    # Product URL routing ✅
│   ├── admin.py                   # Admin configuration ✅
│   ├── templates/products/        # Product HTML templates ✅
│   │   ├── home.html
│   │   ├── category_detail.html
│   │   ├── product_detail.html
│   │   └── search_results.html
│   └── migrations/                # Database migrations
│
├── users/                          # Users app
│   ├── models.py                  # User profiles ✅
│   ├── admin.py                   # Admin config ✅
│   └── migrations/
│
├── orders/                         # Orders app
│   ├── models.py                  # Order, Cart models ✅
│   ├── admin.py                   # Admin config ✅
│   └── migrations/
│
├── templates/
│   └── base.html                  # Base template with CSS ✅
│
├── static/                         # Static files (CSS, JS)
├── media/                          # User uploads (images)
├── manage.py                       # Django management ✅
├── requirements.txt               # Dependencies ✅
├── README.md                       # Full documentation ✅
└── .env.example                   # Environment variables ✅
```

---

## Key Technologies

- **Django 4.2** - Web framework
- **PostgreSQL** - Database (recommended)
- **SQLite** - Database (quick start)
- **Pillow** - Image handling
- **Django REST Framework** - API ready

---

## Support Resources

- Django Documentation: https://docs.djangoproject.com/
- Django Models: https://docs.djangoproject.com/en/4.2/topics/db/models/
- Django Admin: https://docs.djangoproject.com/en/4.2/ref/contrib/admin/
- PostgreSQL: https://www.postgresql.org/docs/
- Flutterwave API: https://developer.flutterwave.com/

---

## Success Checklist

- [ ] System running: `python manage.py runserver`
- [ ] Admin accessible: http://localhost:8000/admin/
- [ ] Superuser created
- [ ] Sample category added
- [ ] Sample product added
- [ ] Home page loads: http://localhost:8000/
- [ ] Product appears on homepage
- [ ] Product details page works
- [ ] Search functionality works

---

## What's Ready for You to Build Next

1. **User Authentication** - Form views and templates
2. **Shopping Cart** - Add to cart, view cart, checkout page
3. **Payment** - Flutterwave integration
4. **Order Management** - Order confirmation, tracking
5. **User Accounts** - Profile, order history, settings
6. **Wishlist** - Add to favorites functionality
7. **Product Reviews** - Allow users to review products
8. **Admin Features** - Inventory management, reports

All models are ready. Just build the views and templates!

---

## Happy Coding! 🚀

Your AMFIT e-commerce platform is ready for development.
Start with user authentication, then shopping cart, then payments.

Questions? Check the README.md for detailed documentation.
