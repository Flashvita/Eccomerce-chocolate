from django.contrib import admin
from .models import Category, Product, Customer, OrderItem, Order, Notification


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['title', 'id', ]
    prepopulated_fields = {'slug': ('title',)}


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'id']

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['recipient']



@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'price', 'manufacturer', 'quantity']
    prepopulated_fields = {'slug': ('title',)}
    list_filter = ['category', 'price', 'manufacturer']

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    raw_id_fields = ['product']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'customer', 'address', 'postal_code', 'city',
                    'paid', 'created_at', 'buying_type', 'status', ]
    list_filter = ['paid', 'buying_type', 'created_at', 'status', ]
    inlines = [OrderItemInline]
