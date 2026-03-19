from django.test import TestCase
from django.contrib.auth.models import User
from products.models import Category, Subcategory, Product
from .models import Order, OrderItem, Cart, CartItem


class OrderModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.order = Order.objects.create(
            order_number='ORD-001',
            user=self.user,
            status='pending',
            payment_status='pending',
            shipping_address='123 Main St',
            shipping_city='Lagos',
            shipping_state='Lagos',
            shipping_zip='100001',
            shipping_country='Nigeria',
            subtotal=10000,
            total=10000
        )

    def test_order_creation(self):
        self.assertEqual(self.order.order_number, 'ORD-001')
        self.assertEqual(self.order.user, self.user)
        self.assertEqual(self.order.status, 'pending')


class CartModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.cart = Cart.objects.create(user=self.user)
        
        self.category = Category.objects.create(name='Medical', slug='medical')
        self.subcategory = Subcategory.objects.create(
            name='Vitamins',
            category=self.category,
            slug='vitamins'
        )
        self.product = Product.objects.create(
            name='Vitamin C',
            description='Vitamin C supplement',
            price=5000,
            category=self.category,
            subcategory=self.subcategory,
            slug='vitamin-c',
            sku='VIT-C-001'
        )

    def test_cart_creation(self):
        self.assertEqual(self.cart.user, self.user)

    def test_add_item_to_cart(self):
        cart_item = CartItem.objects.create(
            cart=self.cart,
            product=self.product,
            quantity=2
        )
        self.assertEqual(cart_item.quantity, 2)
        self.assertEqual(cart_item.total, 10000)
