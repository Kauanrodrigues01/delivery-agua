from django.contrib import admin

from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
	model = OrderItem
	extra = 0
	fields = ('product', 'quantity', 'unit_price')
	readonly_fields = ('unit_price',)

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
	list_display = ('id', 'customer_name', 'phone', 'status', 'created_at')
	list_filter = ('status', 'created_at')
	search_fields = ('customer_name', 'phone', 'address')
	inlines = [OrderItemInline]
	readonly_fields = ('created_at',)
	fieldsets = (
		('Dados do Cliente', {
			'fields': ('customer_name', 'phone', 'address')
		}),
		('Status e Datas', {
			'fields': ('status', 'created_at')
		}),
	)

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
	list_display = ('order', 'product', 'quantity', 'unit_price')
	search_fields = ('product__name',)
	readonly_fields = ('unit_price',)
	fieldsets = (
		(None, {
			'fields': ('order', 'product', 'quantity', 'unit_price')
		}),
	)
