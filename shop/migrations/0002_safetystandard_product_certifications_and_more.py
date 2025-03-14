# Generated by Django 5.1.5 on 2025-02-19 06:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='SafetyStandard',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('description', models.TextField(blank=True)),
            ],
        ),
        migrations.AddField(
            model_name='product',
            name='certifications',
            field=models.CharField(blank=True, choices=[('CE', 'CE Certified'), ('ANSI', 'ANSI Certified'), ('ISO', 'ISO Certified'), ('OSHA', 'OSHA Compliant')], max_length=20),
        ),
        migrations.AddField(
            model_name='product',
            name='color_options',
            field=models.CharField(blank=True, help_text='Available colors separated by commas', max_length=200),
        ),
        migrations.AddField(
            model_name='product',
            name='featured',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='product',
            name='features',
            field=models.TextField(blank=True, help_text='Key features and specifications of the PPE'),
        ),
        migrations.AddField(
            model_name='product',
            name='material',
            field=models.CharField(blank=True, help_text='Main material of the PPE', max_length=100),
        ),
        migrations.AddField(
            model_name='product',
            name='minimum_order',
            field=models.IntegerField(default=1, help_text='Minimum order quantity'),
        ),
        migrations.AddField(
            model_name='product',
            name='size_unit',
            field=models.CharField(choices=[('US', 'US Size'), ('UK', 'UK Size'), ('EU', 'EU Size'), ('UNIVERSAL', 'Universal Size')], default='UNIVERSAL', max_length=20),
        ),
        migrations.AddField(
            model_name='product',
            name='weight',
            field=models.DecimalField(blank=True, decimal_places=2, help_text='Weight in kg', max_digits=6, null=True),
        ),
        migrations.AlterField(
            model_name='product',
            name='description',
            field=models.TextField(blank=True, max_length=500),
        ),
        migrations.AlterField(
            model_name='product',
            name='discount',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=10),
        ),
        migrations.AlterField(
            model_name='product',
            name='price',
            field=models.DecimalField(decimal_places=2, max_digits=10),
        ),
        migrations.AddField(
            model_name='product',
            name='safety_standards',
            field=models.ManyToManyField(blank=True, to='shop.safetystandard'),
        ),
    ]
