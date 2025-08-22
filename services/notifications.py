from django.conf import settings

from services.evolution import EvolutionAPI
from services.callmebot import CallMeBot


def send_order_notifications(order):
    """
    Envia mensagens WhatsApp para o admin e para o cliente após o checkout.
    """
    evolution = EvolutionAPI()
    admin_number = settings.WHATSAPP_ADMIN_NUMBER
    client_number = order.phone

    # Monta a lista de itens com quantidade
    itens_str = "\n".join(
        [f"- {item.product.name} (x{item.quantity})" for item in order.items.all()]
    )

    # Mensagem para o admin
    admin_message = (
        f"Novo pedido recebido!\n"
        f"Cliente: {order.customer_name}\n"
        f"Telefone: {order.phone}\n"
        f"Endereço: {order.address}\n"
        f"Itens:\n{itens_str}\n"
        f"Total: R$ {order.total_price}\n"
    )
    evolution.send_text_message(admin_number, admin_message)

    # Mensagem para o cliente
    client_message = (
        f"Olá {order.customer_name}, seu pedido foi confirmado!\n"
        f"Resumo do pedido:\n"
        f"Total: R$ {order.total_price}\n"
        f"Em breve entraremos em contato para entrega."
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
        [f"- {item.product.name} (x{item.quantity})" for item in order.items.all()]
    )

    # Mensagem para o admin
    message = (
        f"Novo pedido recebido!\n"
        f"Cliente: {order.customer_name}\n"
        f"Telefone: {order.phone}\n"
        f"Endereço: {order.address}\n"
        f"Itens:\n{itens_str}\n"
        f"Total: R$ {order.total_price}\n"
    )
    callmebot.send_text_message(message)
