from django.contrib import admin

from .models import Cart, CartItem


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    fields = ("product", "quantity", "added_at")
    readonly_fields = ("added_at",)


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("id", "created_at")
    inlines = [CartItemInline]
    readonly_fields = ("created_at",)
    fieldsets = ((None, {"fields": ("created_at",)}),)


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ("cart", "product", "quantity", "added_at")
    search_fields = ("product__name",)
    readonly_fields = ("added_at",)
    fieldsets = ((None, {"fields": ("cart", "product", "quantity", "added_at")}),)
