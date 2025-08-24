from products.models import Product
from checkout.models import Order, OrderItem
from dashboard.utils.metrics import calculate_metrics


def populate_database():
    # Limpar o banco de dados
    Product.objects.all().delete()
    Order.objects.all().delete()

    # Criar produtos
    product1 = Product.objects.create(name="Produto 1", price=10.00, is_active=True)
    product2 = Product.objects.create(name="Produto 2", price=20.00, is_active=False)
    product3 = Product.objects.create(name="Produto 3", price=30.00, is_active=True)

    # Criar pedidos
    order1 = Order.objects.create(
        customer_name="Cliente 1",
        phone="123456789",
        address="Endereço 1",
        status="completed",
    )
    order2 = Order.objects.create(
        customer_name="Cliente 2",
        phone="987654321",
        address="Endereço 2",
        status="completed",
    )

    # Adicionar itens aos pedidos
    OrderItem.objects.create(order=order1, product=product1, quantity=2)
    OrderItem.objects.create(order=order1, product=product3, quantity=1)
    OrderItem.objects.create(order=order2, product=product2, quantity=3)


def expect_metrics():
    return {
        "total_products": 3,
        "total_active_products": 2,
        "total_inactive_products": 1,
        "total_sales": 2,
        "total_revenue": 110.00,  # (2*10 + 1*30) + (3*20)
        "ticket_medio": 55.00,  # 110 / 2
        "sales_last_7_days": 2,
        "revenue_last_7_days": 110.00,
        "sales_last_30_days": 2,
        "revenue_last_30_days": 110.00,
    }


def test_metrics():
    populate_database()
    calculated = calculate_metrics()
    expected = expect_metrics()

    assert calculated == expected, (
        f"Metrics do not match!\nCalculated: {calculated}\nExpected: {expected}"
    )
    print("All metrics match successfully!")
