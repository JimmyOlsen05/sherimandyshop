from django.contrib import admin
from .models import MobileMoneyPayment

# Register your models here.

@admin.register(MobileMoneyPayment)
class MobileMoneyPaymentAdmin(admin.ModelAdmin):
    list_display = ['reference', 'order', 'amount', 'phone_number', 'network', 'status', 'created_at']
    list_filter = ['status', 'network', 'created_at']
    search_fields = ['reference', 'phone_number', 'order__id']
    readonly_fields = ['reference', 'created_at', 'updated_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Payment Information', {
            'fields': ('order', 'amount', 'phone_number', 'network')
        }),
        ('Status', {
            'fields': ('status', 'transaction_id')
        }),
        ('System Information', {
            'fields': ('reference', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
