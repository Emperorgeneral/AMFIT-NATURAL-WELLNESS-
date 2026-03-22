from django.test import TestCase
from .models import Category, Subcategory, Product


class CategoryModelTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name='Medical',
            slug='medical',
            description='Medical products'
        )

    def test_category_creation(self):
        self.assertEqual(self.category.name, 'Medical')
        self.assertEqual(str(self.category), 'Medical')


class SubcategoryModelTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name='Medical',
            slug='medical'
        )
        self.subcategory = Subcategory.objects.create(
            name='Vitamins',
            category=self.category,
            slug='vitamins'
        )

    def test_subcategory_creation(self):
        self.assertEqual(self.subcategory.name, 'Vitamins')
        self.assertEqual(self.subcategory.category, self.category)


class ProductModelTest(TestCase):
    def setUp(self):
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
            sku='VIT-C-001',
            stock_quantity=100
        )

    def test_product_creation(self):
        self.assertEqual(self.product.name, 'Vitamin C')
        self.assertEqual(self.product.price, 5000)
        self.assertFalse(self.product.is_on_sale)

    def test_product_on_sale(self):
        self.product.discounted_price = 4000
        self.product.save()
        self.assertTrue(self.product.is_on_sale)
        self.assertEqual(self.product.discount_percentage, 20.0)
