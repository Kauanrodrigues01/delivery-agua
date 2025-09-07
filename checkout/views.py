from django.shortcuts import render
from django.views.generic import TemplateView

from cart.views import get_cart
from services.notifications import (
    send_order_notifications_with_callmebot,
)

from .models import Order, OrderItem


class CheckoutView(TemplateView):
    template_name = "checkout/checkout.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cart = get_cart(self.request)
        cart_items = cart.items.select_related("product").all()
        total = sum(item.product.price * item.quantity for item in cart_items)
        context["cart_total"] = total
        context["cart_items"] = cart_items
        context["cart_count"] = cart.items.count()
        return context

    def post(self, request, *args, **kwargs):
        cart = get_cart(request)
        cart_items = cart.items.select_related("product").all()
        total = sum(item.product.price * item.quantity for item in cart_items)
        name = request.POST.get("name")
        phone = request.POST.get("phone")
        address = request.POST.get("address")
        payment_method = request.POST.get("payment_method")
        cash_value = request.POST.get("cash_value")
        context = self.get_context_data()

        # Validação do troco
        if payment_method == "dinheiro":
            try:
                cash_value = float(cash_value.replace(",", "."))
            except Exception:
                cash_value = 0
            if cash_value < total:
                return render(request, "checkout/error.html", context)

        try:
            # Cria o pedido
            order = Order.objects.create(
                customer_name=name,
                phone=phone,
                address=address,
            )
            for item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    quantity=item.quantity,
                )
            # Envia notificações WhatsApp
            try:
                send_order_notifications_with_callmebot(order)
                # Limpa o carrinho apenas se a notificação for enviada com sucesso
                cart.items.all().delete()
                context = self.get_context_data()
                return render(request, "checkout/success.html", context)
            except Exception as e:
                # Se falhar, apaga a order criada
                order.delete()
                print(f"Erro ao enviar notificação: {e}")
                return render(request, "checkout/error.html", context)
        except Exception as e:
            print(f"Error processing order: {e}")
            return render(request, "checkout/error.html", context)
