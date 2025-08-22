from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.generic import DetailView, ListView

from cart.models import CartItem
from cart.views import get_cart

from .models import Product


def add_to_cart(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid method"}, status=405)

    product_id = request.POST.get("product_id")
    if not product_id:
        return JsonResponse({"error": "No product id"}, status=400)

    cart = get_cart(request)
    product = get_object_or_404(Product, pk=product_id)
    item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        item.quantity += 1
        item.save()

    return JsonResponse({"success": True, "cart_count": cart.items.count()})


class ProductListView(ListView):
    model = Product
    template_name = "products/product_list.html"
    context_object_name = "products"
    queryset = Product.objects.filter(is_active=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cart = get_cart(self.request)
        context["cart_count"] = cart.items.count() if cart else 0
        return context


class ProductDetailView(DetailView):
    model = Product
    template_name = "products/product_detail.html"
    context_object_name = "product"
