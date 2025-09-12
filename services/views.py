import json
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

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
        # Buscar o pedido pelo payment_id
        order = Order.objects.filter(payment_id=payment_id).first()
        
        if not order:
            return {
                'success': False,
                'message': f'Pedido não encontrado para payment_id: {payment_id}'
            }
        
        # Mapear status do MercadoPago para status do pedido
        if status == 'approved' and status_detail == 'accredited':
            order.payment_status = 'paid'
            order.status = 'completed'
            order.save()
            
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
    Este webhook apenas analisa o status e delega as ações para funções específicas.
    """
    if request.method != 'POST':
        return HttpResponse(status=405)  # Method Not Allowed
    
    try:
        # Parse do JSON recebido
        data = json.loads(request.body.decode('utf-8'))
    except json.JSONDecodeError:
        return HttpResponse("Invalid JSON", status=400)
    
    # Extrair informações básicas
    action = data.get('action')
    if not action:
        return HttpResponse("No action specified", status=400)
    
    # Processar apenas atualizações de pagamento
    if action != 'payment.updated':
        return HttpResponse("Action not supported", status=200)
    
    # Extrair ID do pagamento
    payment_id = data.get('data', {}).get('id')
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
        print(f"Webhook MercadoPago - Payment ID: {payment_id}, Status: {status}/{status_detail}")
        
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


@csrf_exempt
def test_order_status_update(request):
    """
    Endpoint para testar manualmente a atualização de status de pedidos.
    Útil para desenvolvimento e debug.
    
    POST /services/test-order-status/
    {
        "payment_id": "123456789",
        "status": "approved",
        "status_detail": "accredited"
    }
    """
    if request.method != 'POST':
        return HttpResponse("Method not allowed", status=405)
    
    try:
        data = json.loads(request.body.decode('utf-8'))
        
        payment_id = data.get('payment_id')
        status = data.get('status')
        status_detail = data.get('status_detail')
        
        if not all([payment_id, status, status_detail]):
            return HttpResponse("Missing required fields", status=400)
        
        result = update_order_status(
            payment_id=payment_id,
            status=status,
            status_detail=status_detail
        )
        
        return HttpResponse(json.dumps(result, indent=2), 
                          content_type='application/json', 
                          status=200 if result['success'] else 400)
        
    except json.JSONDecodeError:
        return HttpResponse("Invalid JSON", status=400)
    except Exception as e:
        return HttpResponse(f"Error: {str(e)}", status=500)
