from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from products.models import Category, Product, ProductReview, Subcategory


class Command(BaseCommand):
    help = 'Populate the store with sample categories, subcategories, and products.'

    def handle(self, *args, **options):
        medical, _ = Category.objects.get_or_create(
            slug='medical',
            defaults={
                'name': 'Medical',
                'description': 'Clinical and home-care essentials for everyday health management.',
            },
        )
        wellness, _ = Category.objects.get_or_create(
            slug='wellness',
            defaults={
                'name': 'Wellness',
                'description': 'Supplements and daily support products designed for preventative care.',
            },
        )
        family, _ = Category.objects.get_or_create(
            slug='family-care',
            defaults={
                'name': 'Family Care',
                'description': 'Everyday family health, hygiene, and maternal support collections.',
            },
        )

        vitamins, _ = Subcategory.objects.get_or_create(
            category=medical,
            slug='vitamins',
            defaults={'name': 'Vitamins', 'description': 'Targeted nutritional support for immunity and recovery.'},
        )
        fertility, _ = Subcategory.objects.get_or_create(
            category=medical,
            slug='fertility',
            defaults={'name': 'Fertility', 'description': 'Guided reproductive wellness products and support care.'},
        )
        diagnostics, _ = Subcategory.objects.get_or_create(
            category=wellness,
            slug='diagnostics',
            defaults={'name': 'Diagnostics', 'description': 'Reliable home monitoring kits and wellness checks.'},
        )
        maternal, _ = Subcategory.objects.get_or_create(
            category=family,
            slug='maternal-care',
            defaults={'name': 'Maternal Care', 'description': 'Supportive essentials for pre and post-natal care.'},
        )

        products = [
            {
                'name': 'Vitamin C Immune Support',
                'slug': 'vitamin-c-immune-support',
                'sku': 'AMF-VIT-001',
                'description': 'A high-strength daily Vitamin C supplement designed to support immunity and antioxidant recovery.',
                'price': '8500.00',
                'discounted_price': '7200.00',
                'stock_quantity': 48,
                'category': medical,
                'subcategory': vitamins,
                'rating': 4.8,
                'review_count': 18,
            },
            {
                'name': 'Prenatal Balance Capsules',
                'slug': 'prenatal-balance-capsules',
                'sku': 'AMF-MAT-002',
                'description': 'Daily prenatal capsules with iron, folate, and essential micronutrients for maternal wellbeing.',
                'price': '18200.00',
                'discounted_price': '16500.00',
                'stock_quantity': 26,
                'category': family,
                'subcategory': maternal,
                'rating': 4.7,
                'review_count': 12,
            },
            {
                'name': 'Ovulation Test Kit Pro',
                'slug': 'ovulation-test-kit-pro',
                'sku': 'AMF-FER-003',
                'description': 'Precision fertility tracking strips packaged for consistent at-home monitoring and planning.',
                'price': '14300.00',
                'stock_quantity': 19,
                'category': medical,
                'subcategory': fertility,
                'rating': 4.5,
                'review_count': 9,
            },
            {
                'name': 'Digital Blood Pressure Monitor',
                'slug': 'digital-blood-pressure-monitor',
                'sku': 'AMF-DIA-004',
                'description': 'Compact upper-arm blood pressure monitor with memory presets for home-based tracking.',
                'price': '32000.00',
                'discounted_price': '28500.00',
                'stock_quantity': 14,
                'category': wellness,
                'subcategory': diagnostics,
                'rating': 4.9,
                'review_count': 21,
            },
            {
                'name': 'Women Wellness Hormone Support',
                'slug': 'women-wellness-hormone-support',
                'sku': 'AMF-FER-005',
                'description': 'Herbal and vitamin blend tailored to support hormonal balance and reproductive health.',
                'price': '15600.00',
                'stock_quantity': 31,
                'category': medical,
                'subcategory': fertility,
                'rating': 4.4,
                'review_count': 7,
            },
            {
                'name': 'Advanced Multivitamin Daily Pack',
                'slug': 'advanced-multivitamin-daily-pack',
                'sku': 'AMF-VIT-006',
                'description': 'A complete multivitamin routine built for busy adults seeking consistent daily support.',
                'price': '12400.00',
                'discounted_price': '10900.00',
                'stock_quantity': 38,
                'category': medical,
                'subcategory': vitamins,
                'rating': 4.6,
                'review_count': 15,
            },
        ]

        for item in products:
            Product.objects.update_or_create(
                slug=item['slug'],
                defaults=item,
            )

        reviewer, _ = User.objects.get_or_create(
            username='amfit_reviewer',
            defaults={
                'email': 'reviewer@amfit.local',
                'first_name': 'AMFIT',
                'last_name': 'Reviewer',
            },
        )

        reviews = [
            ('vitamin-c-immune-support', 5, 'Fast delivery and the product packaging feels premium.'),
            ('digital-blood-pressure-monitor', 5, 'Readings are consistent and setup was straightforward.'),
            ('prenatal-balance-capsules', 4, 'Good daily routine product with clear dosage instructions.'),
        ]

        for slug, rating, comment in reviews:
            product = Product.objects.get(slug=slug)
            ProductReview.objects.update_or_create(
                product=product,
                user=reviewer,
                defaults={'rating': rating, 'comment': comment},
            )

        self.stdout.write(self.style.SUCCESS('Sample store data created or updated successfully.'))