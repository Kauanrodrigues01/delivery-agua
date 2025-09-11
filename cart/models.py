from django.db import models
from django.db.models import F, Sum

from products.models import Product


class Cart(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Carrinho"
        verbose_name_plural = "Carrinhos"

    @property
    def total_quantity(self):
        """Return the total quantity of items in the cart"""
        return self.items.aggregate(total=Sum("quantity"))["total"] or 0

    @property
    def unique_items_count(self):
        """Return the number of unique products in the cart"""
        return self.items.count()

    @property
    def total_price(self):
        """Return the total price of all items in the cart"""
        return (
            self.items.aggregate(total=Sum(F("quantity") * F("product__price")))[
                "total"
            ]
            or 0
        )


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

    class Meta:
        verbose_name = "Item do Carrinho"
        verbose_name_plural = "Itens do Carrinho"
