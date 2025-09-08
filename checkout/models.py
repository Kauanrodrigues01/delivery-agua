from datetime import timedelta

from django.db import models
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
    customer_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    address = models.TextField()
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default="pix")
    cash_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
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
        if self.payment_method == "dinheiro" and self.cash_value:
            return float(self.cash_value) - float(self.total_price)
        return 0

    @property
    def is_late(self):
        elapsed_time = timezone.now() - self.created_at
        return (elapsed_time > timedelta(minutes=25)) and self.status == "pending"

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
