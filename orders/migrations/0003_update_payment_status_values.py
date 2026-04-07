from django.db import migrations, models


def migrate_payment_status_values(apps, schema_editor):
    Order = apps.get_model('orders', 'Order')
    Order.objects.filter(payment_status='completed').update(payment_status='paid')
    Order.objects.filter(payment_status='refunded').update(payment_status='failed')


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0002_add_paystack_reference'),
    ]

    operations = [
        migrations.RunPython(migrate_payment_status_values, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='order',
            name='payment_status',
            field=models.CharField(
                choices=[
                    ('pending', 'Pending'),
                    ('paid', 'Paid'),
                    ('failed', 'Failed'),
                    ('abandoned', 'Abandoned'),
                ],
                default='pending',
                max_length=20,
            ),
        ),
    ]
