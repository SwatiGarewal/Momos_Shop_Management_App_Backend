from django.contrib import admin
from .models import *

# Register your models here.

# ADMIN MASTER SECTION --------------------------------------------
@admin.register(AdminMaster)
class AdminMasterAdmin(admin.ModelAdmin):
    list_display = ['username', 'name', 'active_status']
    exclude = ['account_type']  # yeh field form mein nahi dikhega, auto-set hoga

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(account_type='Admin')

    def save_model(self, request, obj, form, change):
        obj.account_type = 'Admin'
        super().save_model(request, obj, form, change)

# CUSTOMER MASTER SECTION --------------------------------------------
@admin.register(CustomerMaster)
class CustomerMasterAdmin(admin.ModelAdmin):
    list_display = ['username', 'name', 'active_status']
    exclude = ['account_type']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(account_type='Standard')

    def save_model(self, request, obj, form, change):
        obj.account_type = 'Standard'
        super().save_model(request, obj, form, change)

# PRODUCT MASTER ------------------------------------------------
admin.site.register(ProductMaster)

# PAYMENT MODE MASTER ------------------------------------------------
admin.site.register(PaymentModeMaster)