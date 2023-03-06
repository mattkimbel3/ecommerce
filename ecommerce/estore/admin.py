from django.contrib import admin
from .models import Item, OrderItem, Order, Payment, Coupon, Address

# Register your models here.

class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'user', 
        'ordered',
        'shipping_address',
        'billing_address',
        'coupon',
        ]

    list_display_links = [
        'user', 
        'shipping_address',
        'billing_address',
        'coupon',
        ]

    list_filter = ['ordered']

    search_fields = [
        'user__username',
        'ref_code'
    ]

class AddressAdmin(admin.ModelAdmin):

    list_display = [
        'user',
        'street_address',
        'apartment_address',
        'zip_code',
        'address_type', 
        'country', 
    ]
    list_filter = ['address_type', 'country']
    search_fields = ['user', 'street_address', 'apartment_address', 'zip_code']


admin.site.register(Item)
admin.site.register(OrderItem)
admin.site.register(Order, OrderAdmin)
admin.site.register(Payment)
admin.site.register(Coupon)
admin.site.register(Address, AddressAdmin)



