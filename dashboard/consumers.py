import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import AnonymousUser


class OrdersConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Verificar se o usuário está autenticado
        if self.scope["user"] == AnonymousUser():
            await self.close()
            return

        # Adicionar ao grupo de pedidos
        self.group_name = "orders_updates"

        await self.channel_layer.group_add(self.group_name, self.channel_name)

        await self.accept()

    async def disconnect(self, close_code):
        # Remover do grupo
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        # Não precisamos processar mensagens do cliente para este caso
        pass

    # Receber mensagem de atualização de pedido
    async def order_update(self, event):
        # Enviar mensagem para WebSocket
        await self.send(
            text_data=json.dumps({"type": "order_update", "data": event["data"]})
        )

    # Receber mensagem de novo pedido
    async def new_order(self, event):
        # Enviar mensagem para WebSocket
        await self.send(
            text_data=json.dumps({"type": "new_order", "data": event["data"]})
        )

    # Receber mensagem de item adicionado
    async def order_item_added(self, event):
        # Enviar mensagem para WebSocket
        await self.send(
            text_data=json.dumps({"type": "order_item_added", "data": event["data"]})
        )

    # Receber mensagem de item removido
    async def order_item_removed(self, event):
        # Enviar mensagem para WebSocket
        await self.send(
            text_data=json.dumps({"type": "order_item_removed", "data": event["data"]})
        )
