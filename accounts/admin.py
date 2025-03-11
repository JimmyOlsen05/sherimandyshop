from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html

from .models import Account, UserProfile


class AccountAdmin(UserAdmin):
    list_display = ('email', 'username', 'first_name', 'last_name', 'last_login', 'is_active')
    readonly_fields = ('date_joined', 'last_login')
    ordering = ('-date_joined',)
    list_filter = ('is_active', 'is_staff')
    search_fields = ('email', 'username', 'first_name', 'last_name')
    
    fieldsets = (
        ('Personal Info', {'fields': ('email', 'username', 'password')}),
        ('Personal Details', {'fields': ('first_name', 'last_name', 'phone_number')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_admin', 'is_superadmin')}),
        ('Important Dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2'),
        }),
    )

    filter_horizontal = ()

admin.site.register(Account, AccountAdmin)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    def user_letter(self, object):
        return format_html('<div style="background: linear-gradient(135deg, #4f46e5 0%, #6366f1 100%); width: 30px; height: 30px; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold;">{}</div>', object.user.first_name[0].upper())
    user_letter.short_description = 'Avatar'
    
    list_display = ('user_letter', 'user', 'city', 'state', 'country')
    search_fields = ('user__email', 'user__username', 'city', 'state', 'country')
