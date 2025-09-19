from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView

from cart.views import get_cart
from services.mercadopago import MercadoPagoService
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
        context["cart_total"] = cart.total_price
        context["cart_items"] = cart_items
        context["cart_count"] = cart.total_quantity
        return context

    def post(self, request, *args, **kwargs):
        cart = get_cart(request)
        cart_items = cart.items.select_related("product").all()

        # SEGURANÇA: Verificar se há produtos inativos no carrinho
        inactive_items = cart_items.filter(product__is_active=False)
        if inactive_items.exists():
            context = self.get_context_data()
            context["error_message"] = (
                "Seu carrinho contém produtos que não estão mais disponíveis. Remova-os antes de continuar."
            )
            context["inactive_products"] = [
                item.product.name for item in inactive_items
            ]
            return render(request, "checkout/error.html", context)

        # Filtrar apenas produtos ativos para o checkout
        cart_items = cart_items.filter(product__is_active=True)

        if not cart_items.exists():
            context = self.get_context_data()
            context["error_message"] = (
                "Seu carrinho está vazio ou todos os produtos estão indisponíveis."
            )
            return render(request, "checkout/error.html", context)

        total = cart.total_price  # Usando a propriedade do modelo
        name = request.POST.get("name")
        phone = request.POST.get("phone")
        cpf = request.POST.get("cpf", "").strip()
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
                cpf=cpf if cpf else None,
                address=address,
                payment_method=payment_method,
                cash_value=cash_value if payment_method == "dinheiro" else None,
                payment_status="pending",
            )
            for item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    quantity=item.quantity,
                )

            # Envia notificação de novo pedido para todos os métodos de pagamento
            try:
                send_order_notifications_with_callmebot(order)
            except Exception as e:
                print(f"Erro ao enviar notificação de novo pedido: {e}")
                # Não interrompe o fluxo se a notificação falhar

            # Se o pagamento for PIX, cria o pagamento e redireciona
            if payment_method == "pix":
                try:
                    payment_data = create_payment_charge(order)
                    # Salva o ID do pagamento no pedido para rastreamento
                    order.payment_id = payment_data.get("id")
                    order.payment_url = (
                        payment_data.get("point_of_interaction", {})
                        .get("transaction_data", {})
                        .get("ticket_url")
                    )
                    order.save()

                    # Limpa o carrinho e redireciona para página de aguardar pagamento
                    cart.items.all().delete()
                    return redirect("checkout:awaiting_payment", order_id=order.id)
                except Exception as e:
                    order.delete()
                    print(f"Erro ao criar pagamento PIX: {e}")
                    context["error_message"] = (
                        "Erro ao processar pagamento PIX. Tente novamente."
                    )
                    return render(request, "checkout/error.html", context)

            if payment_method == "cartao":
                try:
                    preference_data = create_payment_charge(order)
                    # Salva a URL de pagamento no pedido, pagamento por preferência não gera ID de pagamento imediato, só depois do pagamento no webhook
                    order.payment_id = None
                    order.payment_url = preference_data.get("init_point")
                    order.save()

                    # Limpa o carrinho e redireciona para página de aguardar pagamento
                    cart.items.all().delete()
                    return redirect("checkout:awaiting_payment", order_id=order.id)
                except Exception as e:
                    order.delete()
                    print(f"Erro ao criar pagamento com cartão: {e}")
                    context["error_message"] = (
                        "Erro ao processar pagamento com cartão. Tente novamente."
                    )
                    return render(request, "checkout/error.html", context)

            if payment_method == "dinheiro":
                try:
                    # Limpa o carrinho
                    cart.items.all().delete()
                    return render(request, "checkout/success.html", context)
                except Exception as e:
                    order.delete()
                    print(f"Erro ao processar pagamento em dinheiro: {e}")
                    context["error_message"] = (
                        "Erro ao finalizar pedido. Tente novamente."
                    )
                    return render(request, "checkout/error.html", context)

            # Fallback para outros métodos de pagamento
            cart.items.all().delete()
            context = self.get_context_data()
            return render(request, "checkout/success.html", context)

        except Exception as e:
            print(f"Error processing order: {e}")
            return render(request, "checkout/error.html", context)


def create_payment_charge(order: Order) -> dict:
    """
    Função para criar uma cobrança de pagamento via MercadoPago.
    """

    mp_service = MercadoPagoService()

    if order.payment_method == "pix":
        payment_data = mp_service.pay_with_pix(
            amount=float(order.total_price),
            payer_email="cliente@exemplo.com",
            payer_cpf=order.cpf if order.cpf else "00000000000",
            description=f"Pedido #{order.id} - {order.customer_name}",
        )
        return payment_data

    elif order.payment_method == "cartao":
        # Criar lista de itens para a preferência
        items = []
        for item in order.items.all():
            items.append(
                {
                    "id": str(item.product.id),
                    "title": item.product.name,
                    "quantity": item.quantity,
                    "currency_id": "BRL",
                    "unit_price": float(item.product.price),
                }
            )

        # Usar o método adequado do serviço MercadoPago
        preference_data = mp_service.create_preference_with_card(
            items, order_id=str(order.id)
        )
        return preference_data

    return {}


class AwaitingPaymentView(TemplateView):
    """View para página de aguardando pagamento (PIX e Cartão)"""

    template_name = "checkout/awaiting_payment.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order_id = kwargs.get("order_id")
        order = get_object_or_404(Order, id=order_id)

        # Busca informações do pagamento se existir
        payment_info = None
        ticket_url = order.payment_url

        context.update(
            {
                "order": order,
                "payment_info": payment_info,
                "ticket_url": ticket_url,
            }
        )
        return context


def get_payment_info(payment_id: str) -> dict:
    """
    Função para buscar informações de um pagamento
    """
    mp_service = MercadoPagoService()
    return mp_service.get_payment_info(payment_id)


@csrf_exempt
def check_payment_status(request, order_id):
    """
    API endpoint para verificar status do pagamento via AJAX (PIX e Cartão)
    """
    if request.method == "GET":
        try:
            order = get_object_or_404(Order, id=order_id)

            if not order.payment_id:
                print("DEBUG: pedido sem payment_id")
                return JsonResponse(
                    {
                        "status": "error",
                        "message": "Pagamento não encontrado, caso seja cartão, verifique se o pagamento foi efetuado",
                    }
                )

            payment_info = get_payment_info(order.payment_id)

            return JsonResponse(
                {
                    "status": "success",
                    "payment_status": payment_info.get("status"),
                    "payment_detail": payment_info.get("status_detail"),
                    "ticket_url": payment_info.get("point_of_interaction", {})
                    .get("transaction_data", {})
                    .get("ticket_url"),
                    "qr_code": payment_info.get("point_of_interaction", {})
                    .get("transaction_data", {})
                    .get("qr_code"),
                    "order_paid": order.payment_status == "paid",
                }
            )

        except Exception as e:
            print(f"Erro ao verificar status do pagamento: {e}")
            return JsonResponse({"status": "error", "message": str(e)})

    return JsonResponse({"status": "error", "message": "Método não permitido"})


class SuccessPaymentView(TemplateView):
    """View para página de pagamento bem-sucedido"""

    template_name = "checkout/success_payment.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order_id = kwargs.get("order_id")
        order = get_object_or_404(Order, id=order_id)

        context.update(
            {"order": order, "success_message": "Pagamento realizado com sucesso!"}
        )
        return context


class ErrorPaymentView(TemplateView):
    """View para página de erro no pagamento"""

    template_name = "checkout/error_payment.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order_id = kwargs.get("order_id")

        # Se o order_id for fornecido, busca o pedido
        if order_id:
            try:
                order = get_object_or_404(Order, id=order_id)
                context["order"] = order
            except:
                pass

        # Pega a mensagem de erro da URL se existir
        error_message = self.request.GET.get(
            "message", "Ocorreu um erro no processamento do pagamento."
        )
        context["error_message"] = error_message

        return context
