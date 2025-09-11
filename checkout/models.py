from datetime import timedelta

from django.db import models
from django.db.models import F, Sum
from django.utils import timezone

from products.models import Product


class OrderQuerySet(models.QuerySet):
    def late(self):
        cutoff_time = timezone.now() - timedelta(minutes=25)
        return self.filter(status="pending", created_at__lt=cutoff_time)

    def pending(self):
        return self.filter(status="pending")

    def completed(self):
        return self.filter(status="completed")

    def cancelled(self):
        return self.filter(status="cancelled")

    def payment_pending(self):
        return self.filter(payment_status="pending")

    def paid(self):
        return self.filter(payment_status="paid")

    def payment_cancelled(self):
        return self.filter(payment_status="cancelled")

    def today(self):
        """Pedidos criados hoje"""
        from datetime import datetime, time

        from django.utils import timezone

        today_date = timezone.localtime().date()
        today_start = timezone.make_aware(datetime.combine(today_date, time.min))
        today_end = timezone.make_aware(datetime.combine(today_date, time.max))

        return self.filter(created_at__gte=today_start, created_at__lte=today_end)

    def effective(self):
        """Pedidos efetivos (completed + paid)"""
        return self.filter(status="completed", payment_status="paid")

    def last_days(self, days):
        """Pedidos dos últimos N dias"""
        cutoff = timezone.now() - timedelta(days=days)
        return self.filter(created_at__gte=cutoff)

    def total_revenue(self):
        """Calcula receita total dos pedidos no queryset de forma otimizada"""

        total = self.aggregate(
            total_revenue=Sum(F("items__quantity") * F("items__product__price"))
        )["total_revenue"]

        return float(total) if total else 0.0

    def daily_revenue_last_days(self, days):
        """
        Retorna lista com receita diária dos últimos N dias para gráficos
        Formato: [valor_dia_1, valor_dia_2, ..., valor_dia_N]
        """
        from collections import defaultdict
        from decimal import Decimal

        # Buscar pedidos dos últimos N dias com agregação otimizada
        cutoff = timezone.now() - timedelta(days=days)

        orders_with_totals = (
            self.filter(created_at__gte=cutoff)
            .annotate(total=Sum(F("items__quantity") * F("items__product__price")))
            .values("created_at__date", "total")
        )

        # Organizar por data
        daily_data = defaultdict(lambda: Decimal("0"))

        for order_data in orders_with_totals:
            date_key = order_data["created_at__date"]
            if order_data["total"]:
                daily_data[date_key] += Decimal(str(order_data["total"]))

        # Gerar lista dos últimos N dias (mesmo se não houver vendas)
        result = []
        for i in range(days):
            target_date = (timezone.now() - timedelta(days=days - 1 - i)).date()
            # Converter para float para compatibilidade com Chart.js
            result.append(float(daily_data.get(target_date, Decimal("0"))))

        return result


class Order(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]
    PAYMENT_CHOICES = [
        ("pix", "PIX"),
        ("dinheiro", "Dinheiro"),
        ("cartao", "Cartão"),
    ]
    PAYMENT_STATUS_CHOICES = [
        ("pending", "Pendente"),
        ("paid", "Pago"),
        ("cancelled", "Cancelado/Devolvido"),
    ]
    customer_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    address = models.TextField()
    payment_method = models.CharField(
        max_length=20, choices=PAYMENT_CHOICES, default="pix"
    )
    cash_value = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    payment_status = models.CharField(
        max_length=20, choices=PAYMENT_STATUS_CHOICES, default="pending"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")

    objects = OrderQuerySet.as_manager()

    def __str__(self):
        return f"Order #{self.id} - {self.customer_name}"

    @property
    def total_price(self):
        return sum(item.quantity * item.product.price for item in self.items.all())

    @property
    def change_amount(self):
        """Calcula o troco quando o pagamento é em dinheiro"""
        from decimal import Decimal

        if self.payment_method == "dinheiro" and self.cash_value:
            return max(Decimal("0.00"), self.cash_value - self.total_price)
        return Decimal("0.00")

    @property
    def is_payment_pending(self):
        """Verifica se o pagamento está pendente"""
        return self.payment_status == "pending"

    @property
    def is_paid(self):
        """Verifica se o pagamento foi realizado"""
        return self.payment_status == "paid"

    @property
    def is_late(self):
        elapsed_time = timezone.now() - self.created_at
        return (elapsed_time > timedelta(minutes=25)) and self.status == "pending"

    @property
    def is_finalized(self):
        """Verifica se o pedido está finalizado (concluído e pago) - não pode mais ser alterado"""
        return self.status == "completed" and self.payment_status == "paid"

    @property
    def can_edit_items(self):
        """Verifica se é possível editar itens (adicionar/remover produtos) do pedido"""
        return self.payment_status != "paid"

    @property
    def can_edit_basic_info(self):
        """Verifica se é possível editar informações básicas (nome, endereço, etc.)"""
        return not self.is_finalized and not self.is_totally_cancelled

    @property
    def is_totally_cancelled(self):
        """Verifica se o pedido está totalmente cancelado (status e pagamento cancelados)"""
        return self.status == "cancelled" and self.payment_status == "cancelled"

    class Meta:
        verbose_name = "Pedido"
        verbose_name_plural = "Pedidos"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

    class Meta:
        verbose_name = "Item do Pedido"
        verbose_name_plural = "Itens do Pedido"
