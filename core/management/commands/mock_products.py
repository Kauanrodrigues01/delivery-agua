import random
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError

from products.models import Product, Category


class Command(BaseCommand):
    help = "Create mock products for testing purposes"

    # Lista de produtos variados com nomes e preços até 30 reais
    PRODUCTS_DATA = [
        {"name": "Hambúrguer Artesanal", "price": "15.90", "description": "Hambúrguer artesanal com pão brioche, carne 180g e molho especial"},
        {"name": "Pizza Margherita", "price": "28.50", "description": "Pizza tradicional com molho de tomate, mussarela e manjericão"},
        {"name": "Açaí na Tigela 500ml", "price": "12.90", "description": "Açaí cremoso com granola, banana e mel"},
        {"name": "Sanduíche Natural", "price": "8.90", "description": "Sanduíche natural com peito de peru, alface e tomate"},
        {"name": "Suco Detox 300ml", "price": "9.50", "description": "Suco natural detox com couve, limão e gengibre"},
        {"name": "Pastel Assado", "price": "6.50", "description": "Pastel assado com recheio de frango ou queijo"},
        {"name": "Café Gourmet", "price": "4.90", "description": "Café especial torrado na hora"},
        {"name": "Tapioca Completa", "price": "11.90", "description": "Tapioca com queijo, presunto e ovos"},
        {"name": "Vitamina de Frutas", "price": "7.50", "description": "Vitamina natural com frutas da estação"},
        {"name": "Coxinha Gourmet", "price": "5.90", "description": "Coxinha artesanal com recheio de frango desfiado"},
        {"name": "Pão de Açúcar", "price": "3.50", "description": "Pão doce tradicional fresquinho"},
        {"name": "Água Mineral 500ml", "price": "2.50", "description": "Água mineral natural sem gás"},
        {"name": "Refrigerante Lata", "price": "4.50", "description": "Refrigerante gelado diversos sabores"},
        {"name": "Marmita Fitness", "price": "18.90", "description": "Marmita saudável com frango grelhado, arroz integral e legumes"},
        {"name": "Brownie Caseiro", "price": "8.50", "description": "Brownie caseiro com chocolate belga"},
        {"name": "Salada Caesar", "price": "16.90", "description": "Salada caesar com frango grelhado e molho especial"},
        {"name": "Wrap de Frango", "price": "13.50", "description": "Wrap integral com frango desfiado e vegetais"},
        {"name": "Milkshake de Morango", "price": "9.90", "description": "Milkshake cremoso sabor morango"},
        {"name": "Torta de Limão", "price": "7.90", "description": "Fatia de torta de limão com merengue"},
        {"name": "Empada de Palmito", "price": "6.90", "description": "Empada artesanal com recheio de palmito"},
    ]

    def add_arguments(self, parser):
        parser.add_argument(
            "--count", type=int, default=15, help="Number of mock products to create (max 20 available)"
        )
        return super().add_arguments(parser)


    def handle(self, *args, **kwargs):
        count = min(kwargs.get("count", 15), len(self.PRODUCTS_DATA))

        try:
            # Verificar se existe alguma categoria, criar uma padrão se necessário
            category = None
            if Category.objects.exists():
                category = Category.objects.first()
                self.stdout.write(f"Usando categoria existente: {category.name}")
            else:
                category = Category.objects.create(
                    name="Produtos",
                    description="Produtos variados"
                )
                self.stdout.write(f"Categoria criada: {category.name}")

            created_count = 0

            # Selecionar produtos aleatórios da lista
            selected_products = random.sample(self.PRODUCTS_DATA, count)

            for product_data in selected_products:
                # Verificar se o produto já existe
                if Product.objects.filter(name=product_data["name"]).exists():
                    self.stdout.write(f"Produto '{product_data['name']}' já existe, pulando...")
                    continue

                product = Product.objects.create(
                    name=product_data["name"],
                    description=product_data["description"],
                    price=Decimal(product_data["price"]),
                    category=category,
                    is_active=True
                )

                created_count += 1
                self.stdout.write(f"✓ Produto criado: {product.name} - R$ {product.price}")

            self.stdout.write(
                self.style.SUCCESS(f"Successfully created {created_count} mock products.")
            )

            # Mostrar estatísticas
            total_products = Product.objects.count()
            self.stdout.write(f"Total de produtos no sistema: {total_products}")

        except Exception as e:
            raise CommandError(f"Error creating mock products: {e}")
