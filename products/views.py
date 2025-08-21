

from django.views.generic import DetailView, ListView

from cart.views import get_cart
from django.shortcuts import redirect
from cart.models import Cart, CartItem

def add_to_cart(request, product_id):
	cart = get_cart(request)
	product = Product.objects.get(pk=product_id)
	item, created = CartItem.objects.get_or_create(cart=cart, product=product)
	if not created:
		item.quantity += 1
		item.save()
	return None

from .models import Product


class ProductListView(ListView):
	model = Product
	template_name = 'products/product_list.html'
	context_object_name = 'products'
	queryset = Product.objects.filter(is_active=True)

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		cart = get_cart(self.request)
		context['cart_count'] = cart.items.count() if cart else 0
		return context

class ProductDetailView(DetailView):
	model = Product
	template_name = 'products/product_detail.html'
	context_object_name = 'product'
