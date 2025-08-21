

from django.views.generic import DetailView, ListView

from cart.views import get_cart

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
