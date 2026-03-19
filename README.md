# AMFIT E-Commerce Backend

A Django-based e-commerce platform with product management, user authentication, and shopping cart functionality.

## Project Structure

```
amfit_ecommerce/
├── amfit/                      # Main Django project settings
│   ├── settings.py            # Project configuration
│   ├── urls.py                # Main URL routing
│   ├── wsgi.py                # WSGI configuration
│   └── asgi.py                # ASGI configuration
├── products/                  # Products application
│   ├── models.py              # Product, Category, Subcategory, Review models
│   ├── views.py               # Product browsing views
│   ├── urls.py                # Product URL routing
│   ├── admin.py               # Admin dashboard configuration
│   └── templates/products/    # Product templates (HTML)
├── users/                     # User management application
│   ├── models.py              # UserProfile, VerificationToken models
│   ├── admin.py               # User admin configuration
│   └── migrations/
├── orders/                    # Orders application
│   ├── models.py              # Order, OrderItem, Cart, CartItem models
│   ├── admin.py               # Orders admin configuration
│   └── migrations/
├── templates/                 # Base templates
│   └── base.html              # Base template (header, footer, CSS)
├── manage.py                  # Django management script
└── requirements.txt           # Python dependencies
```

## Database Schema

### Products App

**Category**
- name
- description
- image
- slug
- created_at, updated_at

**Subcategory**
- name
- category (FK)
- description
- image
- slug
- created_at, updated_at

**Product**
- name
- description
- price
- discounted_price (optional)
- category (FK)
- subcategory (FK)
- image
- stock_quantity
- status (active/inactive/discontinued)
- slug
- sku (unique)
- rating
- review_count
- created_at, updated_at

**ProductReview**
- product (FK)
- user (FK)
- rating (1-5)
- comment
- created_at, updated_at

### Users App

**UserProfile**
- user (OneToOne)
- phone
- address, city, state, zip_code, country
- date_of_birth
- profile_image
- created_at, updated_at

**VerificationToken**
- user (OneToOne)
- token
- verified
- created_at, expires_at

### Orders App

**Order**
- order_number (unique)
- user (FK)
- status (pending/processing/shipped/delivered/cancelled)
- payment_status (pending/completed/failed/refunded)
- shipping_address, city, state, zip, country
- subtotal, shipping_cost, tax, total
- notes, tracking_number
- created_at, updated_at

**OrderItem**
- order (FK)
- product (FK)
- quantity
- price (at time of purchase)
- total

**Cart**
- user (OneToOne)
- created_at, updated_at

**CartItem**
- cart (FK)
- product (FK)
- quantity
- added_at

## Installation & Setup

### Prerequisites
- Python 3.8+
- PostgreSQL 12+
- pip (Python package manager)

### Step 1: Clone Repository
```bash
cd amfit_ecommerce
```

### Step 2: Create Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Configure Database
Edit `.env` or set environment variables:
```bash
# PostgreSQL Configuration
DB_NAME=amfit_db
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
```

Or modify `amfit/settings.py` directly for development.

### Step 5: Run Migrations
```bash
python manage.py migrate
```

### Step 6: Create Superuser (Admin)
```bash
python manage.py createsuperuser
```

Follow the prompts to enter email and password.

### Step 7: Run Development Server
```bash
python manage.py runserver
```

Server will be available at `http://localhost:8000`

## Usage

### Admin Dashboard
Access the Django admin dashboard at `http://localhost:8000/admin/`
- Add/edit/delete categories, subcategories, and products
- Manage user accounts and orders
- View reviews and customer information

### Frontend Routes

**Products Browsing:**
- `/` - Home page with featured products
- `/categories/` - All categories
- `/category/<slug>/` - Products by category
- `/category/<category_slug>/subcategory/<subcategory_slug>/` - Products by subcategory
- `/product/<slug>/` - Product details
- `/search/?q=<query>` - Search products

## Key Features Implemented

✅ **Product Management**
- Multiple categories and subcategories
- Product details (name, description, image, price, stock)
- Discount pricing system
- Product ratings and reviews
- Product search and filtering

✅ **Admin Dashboard (Django Admin)**
- Full CRUD operations for products
- Category and subcategory management
- Order management with status updates
- User profile management
- Review moderation

✅ **Product Browsing**
- Browse by category and subcategory
- Search functionality
- Price filtering
- Sorting options (newest, price, popularity)
- Pagination (12 products per page)
- Product detail pages with reviews

✅ **User System**
- User profiles with personal information
- Email verification tokens
- User authentication ready

✅ **Orders & Cart**
- Shopping cart model
- Order creation and tracking
- Order items with purchase history
- Payment status tracking

## Next Steps: Payment Integration

When ready to integrate Flutterwave:

1. **Install Flutterwave SDK:**
   ```bash
   pip install flutterwave-python
   ```

2. **Create payment views** - Handle payment initiation and verification

3. **Update order model** - Add Flutterwave transaction ID and reference

4. **Create payment endpoints:**
   - `POST /api/payment/initialize` - Start payment
   - `POST /api/payment/verify` - Verify payment

5. **Update frontend** - Add checkout page and payment form

See documentation in root directory for detailed payment integration guide.

## Configuration Notes

- **SECRET_KEY**: Change in production (currently set for development only)
- **DEBUG**: Set to `False` in production
- **ALLOWED_HOSTS**: Configure for your domain
- **Database**: Configure PostgreSQL credentials
- **Media files**: Uploaded images stored in `/media/` directory
- **Static files**: CSS/JS in `/static/` directory (collect before deployment)

## Development Tools

### Create Sample Data
```bash
python manage.py shell

# In shell:
from products.models import Category, Subcategory, Product
from django.contrib.auth.models import User

# Create categories
cat = Category.objects.create(name="Medical", slug="medical")

# Create subcategories
sub = Subcategory.objects.create(
    category=cat,
    name="Vitamins",
    slug="vitamins"
)

# Create products
Product.objects.create(
    name="Vitamin C",
    price=5000,
    category=cat,
    subcategory=sub,
    slug="vitamin-c",
    sku="VIT-C-001"
)
```

### Run Tests
```bash
python manage.py test
```

### Collect Static Files (Production)
```bash
python manage.py collectstatic
```

## Deployment Checklist

- [ ] Set `DEBUG = False` in settings
- [ ] Update `ALLOWED_HOSTS` with domain
- [ ] Use strong `SECRET_KEY`
- [ ] Configure PostgreSQL production database
- [ ] Set up environment variables securely
- [ ] Run database migrations
- [ ] Collect static files
- [ ] Configure email backend (for notifications)
- [ ] Set up SSL/HTTPS
- [ ] Run security checks: `python manage.py check --deploy`

## Support & Documentation

For detailed setup and API documentation, see:
- Django Docs: https://docs.djangoproject.com/
- Django REST Framework: https://www.django-rest-framework.org/
- PostgreSQL: https://www.postgresql.org/docs/

## License

This project is developed for AMFIT E-Commerce.
