from django.contrib import admin
from .models import HoldingCompany, Brand, Organization

@admin.register(HoldingCompany)
class HoldingCompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_email', 'contact_phone', 'is_active')
    search_fields = ('name', 'contact_email')
    list_filter = ('is_active',)

@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('name', 'holding_company', 'brand_code', 'royalty_percentage', 'is_active')
    search_fields = ('name', 'brand_code')
    list_filter = ('is_active', 'holding_company')
    autocomplete_fields = ['holding_company']

@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'brand', 'owner_name', 'owner_phone', 'is_franchise', 'is_active')
    search_fields = ('name', 'owner_name', 'owner_email', 'owner_phone')
    list_filter = ('is_active', 'is_franchise', 'brand')
    autocomplete_fields = ['brand']
