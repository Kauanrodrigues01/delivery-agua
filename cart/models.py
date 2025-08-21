from django.db import models


from products.models import Product

class Cart(models.Model):
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		verbose_name = 'Carrinho'
		verbose_name_plural = 'Carrinhos'

class CartItem(models.Model):
	cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
	product = models.ForeignKey(Product, on_delete=models.CASCADE)
	quantity = models.PositiveIntegerField(default=1)
	added_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return f"{self.quantity} x {self.product.name}"

	class Meta:
		verbose_name = 'Item do Carrinho'
		verbose_name_plural = 'Itens do Carrinho'
