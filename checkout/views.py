from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import TemplateView
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

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
        context["cart_total"] = cart.total_price
        context["cart_items"] = cart_items
        context["cart_count"] = cart.total_quantity
        return context

    def post(self, request, *args, **kwargs):
        cart = get_cart(request)
        cart_items = cart.items.select_related("product").all()
        total = cart.total_price  # Usando a propriedade do modelo
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

            # Se o pagamento for PIX, cria o pagamento e redireciona
            if payment_method == "pix":
                try:
                    payment_data = create_payment_charge(order)
                    # Salva o ID do pagamento no pedido para rastreamento
                    order.payment_id = payment_data.get('id')
                    order.save()
                    
                    # Limpa o carrinho e redireciona para página de aguardar pagamento
                    cart.items.all().delete()
                    return redirect('checkout:awaiting_payment', order_id=order.id)
                except Exception as e:
                    order.delete()
                    print(f"Erro ao criar pagamento PIX: {e}")
                    context['error_message'] = "Erro ao processar pagamento PIX. Tente novamente."
                    return render(request, "checkout/error.html", context)

            # Para outros métodos de pagamento (dinheiro, etc.)
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


def create_payment_charge(order: Order) -> dict:
    """
    Função para criar uma cobrança de pagamento via MercadoPago.
    """
    from services.mercadopago import MercadoPagoService

    mp_service = MercadoPagoService()

    if order.payment_method == "pix":
        payment_data = mp_service.pay_with_pix(
            amount=float(order.total_price),
            payer_email=f"cliente@exemplo.com",  # Você pode adicionar campo de email no Order
            payer_cpf="00000000000",  # Você pode adicionar campo de CPF no Order
            description=f"Pedido #{order.id} - {order.customer_name}"
        )
        return payment_data

    return {}


class AwaitingPaymentView(TemplateView):
    """View para página de aguardando pagamento PIX"""
    template_name = "checkout/awaiting_payment.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order_id = kwargs.get('order_id')
        order = get_object_or_404(Order, id=order_id)
        
        # Busca informações do pagamento se existir
        payment_info = None
        if order.payment_id:
            try:
                payment_info = get_payment_info(order.payment_id)
            except Exception as e:
                print(f"Erro ao buscar informações do pagamento: {e}")
        
        print(order)
        print(payment_info)
        print(payment_info.get('point_of_interaction', {}).get('transaction_data', {}).get('ticket_url') if payment_info else None)
        
        context.update({
            'order': order,
            'payment_info': payment_info,
            'ticket_url': payment_info.get('point_of_interaction', {}).get('transaction_data', {}).get('ticket_url') if payment_info else None,
        })
        return context


def get_payment_info(payment_id: str) -> dict:
    """
    Função para buscar informações de um pagamento
    """
    from services.mercadopago import MercadoPagoService
    
    mp_service = MercadoPagoService()
    return mp_service.get_payment_info(payment_id)


@csrf_exempt
def check_payment_status(request, order_id):
    """
    API endpoint para verificar status do pagamento via AJAX
    """
    if request.method == 'GET':
        try:
            order = get_object_or_404(Order, id=order_id)
            
            if not order.payment_id:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Pagamento não encontrado'
                })
            
            payment_info = get_payment_info(order.payment_id)
            
            # Atualiza status do pedido se necessário
            if payment_info.get('status') == 'approved':
                order.payment_status = 'paid'
                order.save()
                
                # Envia notificações apenas quando o pagamento for aprovado
                try:
                    send_order_notifications_with_callmebot(order)
                except Exception as e:
                    print(f"Erro ao enviar notificação: {e}")
            
            return JsonResponse({
                'status': 'success',
                'payment_status': payment_info.get('status'),
                'payment_detail': payment_info.get('status_detail'),
                'ticket_url': payment_info.get('point_of_interaction', {}).get('transaction_data', {}).get('ticket_url'),
                'qr_code': payment_info.get('point_of_interaction', {}).get('transaction_data', {}).get('qr_code'),
                'order_paid': order.payment_status == 'paid'
            })
            
        except Exception as e:
            print(f"Erro ao verificar status do pagamento: {e}")
            return JsonResponse({
                'status': 'error', 
                'message': str(e)
            })
    
    return JsonResponse({'status': 'error', 'message': 'Método não permitido'})
