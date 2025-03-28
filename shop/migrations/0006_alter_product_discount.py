# Generated by Django 5.1.5 on 2025-03-14 18:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0005_product_is_featured'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='discount',
            field=models.DecimalField(decimal_places=2, default=0.0, help_text='Discount percentage (0-100)', max_digits=5),
        ),
    ]
