from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView, View
from django.conf import settings

from products.models import Product

from .models import Cart, CartItem

def get_status_debug(request):
    return JsonResponse({"debug": settings.DEBUG})


# AJAX: aumentar quantidade
@require_POST
def increase_cart_item(request):
    product_id = request.POST.get("product_id")
    cart = get_cart(request)
    item = get_object_or_404(CartItem, cart=cart, product_id=product_id)
    item.quantity += 1
    item.save()
    # Calcular novo total
    cart_items = cart.items.select_related("product").all()
    cart_total = cart.total_price
    return JsonResponse(
        {"success": True, "quantity": item.quantity, "cart_total": float(cart_total)}
    )


# AJAX: diminuir quantidade
@require_POST
def decrease_cart_item(request):
    product_id = request.POST.get("product_id")
    cart = get_cart(request)
    item = get_object_or_404(CartItem, cart=cart, product_id=product_id)
    if item.quantity > 1:
        item.quantity -= 1
        item.save()
        cart_items = cart.items.select_related("product").all()
        cart_total = cart.total_price
        return JsonResponse(
            {
                "success": True,
                "quantity": item.quantity,
                "cart_total": float(cart_total),
            }
        )
    else:
        item.delete()
        cart_total = cart.total_price
        return JsonResponse(
            {"success": True, "quantity": 0, "cart_total": float(cart_total)}
        )


# AJAX: remover item
@require_POST
def remove_cart_item(request):
    product_id = request.POST.get("product_id")
    cart = get_cart(request)
    item = get_object_or_404(CartItem, cart=cart, product_id=product_id)
    item.delete()
    cart_total = cart.total_price
    return JsonResponse({"success": True, "cart_total": float(cart_total)})


def get_cart(request):
    cart_id = request.session.get("cart_id")
    if cart_id:
        cart, created = Cart.objects.get_or_create(id=cart_id)
    else:
        cart = Cart.objects.create()
        request.session["cart_id"] = cart.id
    return cart


class AddToCartView(View):
    def post(self, request, *args, **kwargs):
        product_id = request.POST.get("product_id")
        product = get_object_or_404(Product, pk=product_id)
        cart = get_cart(request)
        item, created = CartItem.objects.get_or_create(cart=cart, product=product)
        if not created:
            item.quantity += 1
            item.save()
        return JsonResponse({"success": True, "cart_count": cart.total_quantity})


class CartDetailView(TemplateView):
    template_name = "cart/cart_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cart = get_cart(self.request)
        cart_items = cart.items.select_related("product").all()
        total = cart.total_price
        context["cart"] = cart
        context["cart_items"] = cart_items
        context["cart_count"] = cart.total_quantity
        context["cart_total"] = total
        return context
