from django.shortcuts import render


from django.views.generic import TemplateView, View
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from products.models import Product
from .models import Cart, CartItem

def get_cart(request):
	cart_id = request.session.get('cart_id')
	print(f"Cart ID from session: {cart_id}")
	if cart_id:
		cart, created = Cart.objects.get_or_create(id=cart_id)
	else:
		cart = Cart.objects.create()
		request.session['cart_id'] = cart.id
	return cart

class AddToCartView(View):
	def post(self, request, *args, **kwargs):
		product_id = request.POST.get('product_id')
		product = get_object_or_404(Product, pk=product_id)
		cart = get_cart(request)
		item, created = CartItem.objects.get_or_create(cart=cart, product=product)
		if not created:
			item.quantity += 1
			item.save()
		return JsonResponse({'success': True, 'cart_count': cart.items.count()})

class CartDetailView(TemplateView):
	template_name = 'cart/cart_detail.html'

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		cart = get_cart(self.request)
		context['cart'] = cart
		context['cart_items'] = cart.items.select_related('product').all()
		context['cart_count'] = cart.items.count()
		return context
