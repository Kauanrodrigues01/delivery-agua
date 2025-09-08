from django.contrib import admin

from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ("product", "quantity")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "customer_name", "phone", "payment_method", "status", "created_at")
    list_filter = ("status", "payment_method", "created_at")
    search_fields = ("customer_name", "phone", "address")
    inlines = [OrderItemInline]
    readonly_fields = ("created_at", "total_price", "change_amount")
    fieldsets = (
        ("Dados do Cliente", {"fields": ("customer_name", "phone", "address")}),
        ("Pagamento", {"fields": ("payment_method", "cash_value", "total_price", "change_amount")}),
        ("Status e Datas", {"fields": ("status", "created_at")}),
    )


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("order", "product", "quantity")
    search_fields = ("product__name",)
    fieldsets = ((None, {"fields": ("order", "product", "quantity")}),)
