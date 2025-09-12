import json
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from services.notifications import send_payment_update_notification_with_callmebot

from services.mercadopago import MercadoPagoService
from checkout.models import Order


def update_order_status(payment_id, status, status_detail, date_approved=None, external_reference=None):
    """
    Atualiza o status de um pedido baseado nas informações do pagamento.
    
    Args:
        payment_id: ID do pagamento no MercadoPago
        status: Status do pagamento (approved, pending, cancelled, etc.)
        status_detail: Detalhe do status (accredited, expired, etc.)
        date_approved: Data de aprovação do pagamento
        external_reference: Referência externa (ID do pedido)
    
    Returns:
        dict: Resultado da operação com sucesso/erro e mensagem
    """
    try:
        order = None
        
        # Primeiro, tentar encontrar o pedido pelo payment_id (PIX)
        order = Order.objects.filter(payment_id=payment_id).first()
        print(f"DEBUG - Busca por payment_id {payment_id}: {order}")
        
        # Se não encontrou e tem external_reference, buscar pelo ID do pedido (Cartão)
        if not order and external_reference:
            try:
                print(f"DEBUG - Tentando buscar por external_reference: {external_reference}")
                order = Order.objects.filter(id=int(external_reference)).first()
                print(f"DEBUG - Pedido encontrado por external_reference: {order}")
                # Para cartão, atualizar o payment_id com o ID real do pagamento
                if order and order.payment_method == 'cartao':
                    order.payment_id = payment_id
                    order.save()
                    print(f"DEBUG - Payment_id atualizado para: {payment_id}")
            except (ValueError, TypeError):
                # external_reference não é um número válido
                print(f"DEBUG - External_reference inválido: {external_reference}")
                pass
        
        if not order:
            return {
                'success': False,
                'message': f'Pedido não encontrado para payment_id: {payment_id} ou external_reference: {external_reference}'
            }
        
        # Mapear status do MercadoPago para status do pedido
        if status == 'approved' and status_detail == 'accredited':
            order.payment_status = 'paid'
            order.save()
            
            # Enviar notificações WhatsApp para pagamentos aprovados
            try:
                print(f"DEBUG - Enviando notificação para pedido: {order.id}")
                print(f"DEBUG - Order antes da notificação: ID={order.id}, Nome={order.customer_name}, Phone={order.phone}")
                send_payment_update_notification_with_callmebot(order)
            except Exception as e:
                print(f"Erro ao enviar notificação WhatsApp: {e}")
                import traceback
                traceback.print_exc()
            
            return {
                'success': True,
                'message': f'Pedido #{order.id} marcado como pago e concluído',
                'order_id': order.id,
                'action': 'payment_approved'
            }
            
        elif status == 'cancelled' or (status == 'cancelled' and status_detail == 'expired'):
            order.payment_status = 'cancelled'
            order.status = 'cancelled'
            order.save()
            
            # Enviar notificações WhatsApp para pagamentos cancelados
            try:
                send_payment_update_notification_with_callmebot(order)
            except Exception as e:
                print(f"Erro ao enviar notificação WhatsApp: {e}")
            
            return {
                'success': True,
                'message': f'Pedido #{order.id} cancelado',
                'order_id': order.id,
                'action': 'payment_cancelled'
            }
            
        elif status == 'pending':
            order.payment_status = 'pending'
            order.save()
            
            return {
                'success': True,
                'message': f'Pedido #{order.id} mantido como pendente',
                'order_id': order.id,
                'action': 'payment_pending'
            }
        
        else:
            return {
                'success': True,
                'message': f'Status {status}/{status_detail} não requer ação para pedido #{order.id}',
                'order_id': order.id,
                'action': 'no_action'
            }
            
    except Exception as e:
        return {
            'success': False,
            'message': f'Erro ao atualizar pedido: {str(e)}'
        }


@csrf_exempt
def webhook_mercadopago(request):
    """
    Webhook do MercadoPago para processar atualizações de pagamento.
    Suporta tanto o formato antigo (action/data) quanto o novo (resource/topic).
    """
    if request.method != 'POST':
        return HttpResponse(status=405)  # Method Not Allowed
    
    try:
        # Parse do JSON recebido
        data = json.loads(request.body.decode('utf-8'))
        print(f"Webhook MercadoPago recebido: {data}")
    except json.JSONDecodeError:
        return HttpResponse("Invalid JSON", status=400)
    
    # Verificar formato do webhook
    payment_id = None
    
    # Novo formato: {"resource":"125381511429","topic":"payment"}
    if 'topic' in data and 'resource' in data:
        topic = data.get('topic')
        if topic != 'payment':
            return HttpResponse("Topic not supported", status=200)
        payment_id = data.get('resource')
    
    # Formato antigo: {"action":"payment.updated","data":{"id":"123"}}
    elif 'action' in data and 'data' in data:
        action = data.get('action')
        if action != 'payment.updated':
            return HttpResponse("Action not supported", status=200)
        payment_id = data.get('data', {}).get('id')
    
    else:
        return HttpResponse("Invalid webhook format", status=400)
    
    if not payment_id:
        return HttpResponse("No payment ID", status=400)

    try:
        # Buscar detalhes do pagamento no MercadoPago
        mercado_pago = MercadoPagoService()
        payment_data = mercado_pago.get_payment_info(payment_id)
        
        if not payment_data:
            return HttpResponse("Payment not found", status=404)
        
        # Extrair informações do pagamento
        status = payment_data.get('status')
        status_detail = payment_data.get('status_detail')
        date_approved = payment_data.get('date_approved')
        external_reference = payment_data.get('external_reference')
        
        # Log da operação (para debug)
        print(f"Webhook MercadoPago - Payment ID: {payment_id}, Status: {status}/{status_detail}, External Ref: {external_reference}")
        
        # Atualizar status do pedido
        update_result = update_order_status(
            payment_id=payment_id,
            status=status,
            status_detail=status_detail,
            date_approved=date_approved,
            external_reference=external_reference
        )
        
        if not update_result['success']:
            print(f"Erro ao atualizar pedido: {update_result['message']}")
            return HttpResponse(update_result['message'], status=400)
        
        print(f"Webhook processado com sucesso: {update_result['message']}")
        return HttpResponse("OK", status=200)
        
    except Exception as e:
        print(f"Erro no webhook MercadoPago: {str(e)}")
        return HttpResponse(f"Internal error: {str(e)}", status=500)
