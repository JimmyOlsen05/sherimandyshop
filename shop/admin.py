from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Product, Variation, ReviewRating, ProductGallery, SafetyStandard
import admin_thumbnails

@admin_thumbnails.thumbnail('image')
class ProductGalleryInline(admin.TabularInline):
    model = ProductGallery
    extra = 1


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'display_image']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']
    list_per_page = 20

    def display_image(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" />', obj.image.url)
        return "-"
    display_image.short_description = 'Image'


@admin.register(SafetyStandard)
class SafetyStandardAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    search_fields = ['name', 'description']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'product_image', 'name', 'category', 'price', 'discount', 'stock',
        'certifications', 'is_available', 'featured'
    ]
    list_filter = [
        'is_available', 'featured', 'category', 'new',
        'certifications', 'safety_standards', 'size_unit'
    ]
    list_editable = [
        'price', 'discount', 'stock', 'is_available', 'featured'
    ]
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created', 'updated']
    search_fields = ['name', 'description', 'features', 'material']
    filter_horizontal = ['safety_standards']
    inlines = [ProductGalleryInline]
    list_per_page = 20

    fieldsets = (
        ('Basic Information', {
            'fields': (
                'name', 'slug', 'category', 'description', 
                'features', 'image'
            )
        }),
        ('Pricing & Stock', {
            'fields': (
                'price', 'discount', 'stock', 'minimum_order',
                'is_available', 'featured', 'new'
            )
        }),
        ('PPE Specifications', {
            'fields': (
                'certifications', 'safety_standards', 'material',
                'size_unit', 'weight', 'color_options'
            ),
            'classes': ('collapse',)
        }),
    )

    def product_image(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" />', obj.image.url)
        return "-"
    product_image.short_description = 'Image'

    class Media:
        css = {
            'all': ('css/admin-custom.css',)
        }


@admin.register(Variation)
class VariationAdmin(admin.ModelAdmin):
    list_display = ['product', 'variation_category', 'variation_value', 'is_active']
    list_filter = ['product', 'variation_category', 'is_active']
    list_editable = ['is_active']
    search_fields = ['product__name', 'variation_value']
    list_per_page = 20


@admin.register(ReviewRating)
class ReviewRatingAdmin(admin.ModelAdmin):
    list_display = ['product', 'user', 'rating', 'status', 'created_at']
    list_filter = ['rating', 'status', 'created_at']
    list_editable = ['status']
    search_fields = ['product__name', 'user__email', 'review']
    list_per_page = 20


@admin.register(ProductGallery)
class ProductGalleryAdmin(admin.ModelAdmin):
    list_display = ['product', 'image_preview']
    list_filter = ['product']
    search_fields = ['product__name']
    list_per_page = 20

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" />', obj.image.url)
        return "-"
    image_preview.short_description = 'Image Preview'
