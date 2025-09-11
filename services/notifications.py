from django.conf import settings

from services.callmebot import CallMeBot
from services.evolution import EvolutionAPI


def send_order_notifications(order):
    """
    Envia mensagens WhatsApp para o admin e para o cliente após o checkout.
    """
    evolution = EvolutionAPI()
    admin_number = settings.WHATSAPP_ADMIN_NUMBER
    client_number = order.phone

    # Monta a lista de itens com quantidade
    itens_str = "\n".join(
        [f"  • {item.product.name} (x{item.quantity})" for item in order.items.all()]
    )

    # Informações de pagamento
    payment_method_emoji = {"pix": "💳", "dinheiro": "💰", "cartao": "💳"}.get(
        order.payment_method, "💳"
    )

    payment_status_emoji = {"pending": "⏳", "paid": "✅", "cancelled": "❌"}.get(
        order.payment_status, "⏳"
    )

    payment_info = f"{payment_method_emoji} {order.get_payment_method_display()}"
    payment_info += (
        f"\n{payment_status_emoji} Status: {order.get_payment_status_display()}"
    )

    if order.payment_method == "dinheiro" and order.cash_value:
        change = order.change_amount
        payment_info += f"\nValor recebido: R$ {order.cash_value:.2f}"
        payment_info += f"\nTroco: R$ {change:.2f}"

    # Mensagem para o admin
    admin_message = (
        f"🚨 *NOVO PEDIDO RECEBIDO!*\n\n"
        f"*Cliente:* {order.customer_name}\n"
        f"*Telefone:* {order.phone}\n"
        f"*Endereço:* {order.address}\n\n"
        f"*Itens do pedido:*\n{itens_str}\n\n"
        f"*Total:* R$ {order.total_price:.2f}\n\n"
        f"*Pagamento:*\n{payment_info}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )
    evolution.send_text_message(admin_number, admin_message)

    # Mensagem para o cliente
    client_message = (
        f"✅ *Pedido Confirmado!*\n\n"
        f"Olá *{order.customer_name}*, seu pedido foi confirmado com sucesso!\n\n"
        f"*Resumo do pedido:*\n"
        f"Total: R$ {order.total_price:.2f}\n"
        f"Pagamento: {payment_info}\n\n"
        f"Em breve entraremos em contato para combinar a entrega.\n\n"
        f"Obrigado pela preferência!"
    )
    try:
        evolution.send_text_message(f"55{client_number}", client_message)
    except Exception as e:
        # Apenas loga o erro, não interrompe o fluxo
        print(f"Erro ao enviar mensagem ao cliente: {e}")


def send_order_notifications_with_callmebot(order):
    callmebot = CallMeBot()

    # Monta a lista de itens com quantidade
    itens_str = "\n".join(
        [f"  • {item.product.name} (x{item.quantity})" for item in order.items.all()]
    )

    # Informações de pagamento
    payment_method_emoji = {"pix": "💳", "dinheiro": "💰", "cartao": "💳"}.get(
        order.payment_method, "💳"
    )

    payment_status_emoji = {"pending": "⏳", "paid": "✅", "cancelled": "❌"}.get(
        order.payment_status, "⏳"
    )

    payment_info = f"{payment_method_emoji} {order.get_payment_method_display()}"
    payment_info += (
        f"\n{payment_status_emoji} Status: {order.get_payment_status_display()}"
    )

    if order.payment_method == "dinheiro" and order.cash_value:
        change = order.change_amount
        payment_info += f"\nValor recebido: R$ {order.cash_value:.2f}"
        payment_info += f"\nTroco: R$ {change:.2f}"

    # Mensagem para o admin
    message = (
        f"🚨 *NOVO PEDIDO RECEBIDO!*\n\n"
        f"*Cliente:* {order.customer_name}\n"
        f"*Telefone:* {order.phone}\n"
        f"*Endereço:* {order.address}\n\n"
        f"*Itens do pedido:*\n{itens_str}\n\n"
        f"*Total:* R$ {order.total_price:.2f}\n\n"
        f"*Pagamento:*\n{payment_info}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )
    callmebot.send_text_message(message)
