from datetime import timedelta
from django.utils.timezone import now
from products.models import Product
from checkout.models import Order


# Função para calcular todas as métricas
def calculate_metrics():
    total_products = Product.objects.count()
    total_active_products = Product.objects.filter(is_active=True).count()
    total_inactive_products = Product.objects.filter(is_active=False).count()

    # Excluir pedidos cancelados das métricas de vendas
    active_orders = Order.objects.exclude(status="cancelled")
    total_sales = active_orders.count()
    total_revenue = sum(order.total_price for order in active_orders)
    ticket_medio = total_revenue / total_sales if total_sales > 0 else 0

    # Vendas nos últimos 7 dias (excluindo cancelados)
    last_7_days = now() - timedelta(days=7)
    sales_last_7_days = active_orders.filter(created_at__gte=last_7_days).count()
    revenue_last_7_days = sum(
        order.total_price for order in active_orders.filter(created_at__gte=last_7_days)
    )

    # Vendas nos últimos 30 dias (excluindo cancelados)
    last_30_days = now() - timedelta(days=30)
    sales_last_30_days = active_orders.filter(created_at__gte=last_30_days).count()
    revenue_last_30_days = sum(
        order.total_price
        for order in active_orders.filter(created_at__gte=last_30_days)
    )

    # Pedidos atrasados (pendentes há mais de 25 minutos)
    cutoff_time = now() - timedelta(minutes=25)
    late_orders_count = Order.objects.filter(
        status="pending", 
        created_at__lt=cutoff_time
    ).count()

    return {
        "total_products": total_products,
        "total_active_products": total_active_products,
        "total_inactive_products": total_inactive_products,
        "total_sales": total_sales,
        "total_revenue": total_revenue,
        "ticket_medio": ticket_medio,
        "sales_last_7_days": sales_last_7_days,
        "revenue_last_7_days": revenue_last_7_days,
        "sales_last_30_days": sales_last_30_days,
        "revenue_last_30_days": revenue_last_30_days,
        "late_orders_count": late_orders_count,
    }
