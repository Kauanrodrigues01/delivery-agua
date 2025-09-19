from datetime import timedelta

from django.utils.timezone import now

from checkout.models import Order
from products.models import Product


def get_date_labels(days):
    """
    Gera labels de datas para gráficos
    Formato: ['01/09', '02/09', '03/09', ...]
    """
    labels = []
    for i in range(days):
        target_date = (now() - timedelta(days=days - 1 - i)).date()
        labels.append(target_date.strftime("%d/%m"))
    return labels


# Função para calcular todas as métricas
def calculate_metrics():
    """
    Calcula todas as métricas do dashboard

    CORREÇÕES APLICADAS:
    - revenue_today agora exclui receitas canceladas
    - Gráficos usam queryset base para evitar dupla filtragem
    - Performance otimizada com agregações do Django
    - Otimizado com uma única query usando aggregações condicionais
    """
    from django.db.models import Count, F, Q, Sum

    # ===== MÉTRICAS DO DIA COM OTIMIZAÇÃO =====
    orders_today = Order.objects.today()

    # Uma única query com agregações condicionais para métricas do dia
    today_metrics = orders_today.aggregate(
        total_count=Count('id'),
        pending_count=Count('id', filter=Q(status='pending')),
        completed_count=Count('id', filter=Q(status='completed')),
        cancelled_count=Count('id', filter=Q(status='cancelled')),
        late_count=Count('id', filter=Q(status='pending', created_at__lt=now() - timedelta(minutes=25))),
        revenue_paid=Sum(F('items__quantity') * F('items__product__price'), filter=Q(payment_status='paid')),
        revenue_pending=Sum(F('items__quantity') * F('items__product__price'), filter=Q(payment_status='pending')),
        revenue_cancelled=Sum(F('items__quantity') * F('items__product__price'), filter=Q(payment_status='cancelled')),
    )

    # Extrair valores da agregação
    orders_today_count = today_metrics['total_count'] or 0
    orders_pending_today = today_metrics['pending_count'] or 0
    orders_completed_today = today_metrics['completed_count'] or 0
    orders_cancelled_today = today_metrics['cancelled_count'] or 0
    orders_late_today = today_metrics['late_count'] or 0

    revenue_paid_today = float(today_metrics['revenue_paid'] or 0)
    revenue_pending_today = float(today_metrics['revenue_pending'] or 0)
    revenue_cancelled_today = float(today_metrics['revenue_cancelled'] or 0)
    # CORREÇÃO: Receita real do dia não deve incluir cancelamentos
    revenue_today = revenue_paid_today + revenue_pending_today

    # ===== MÉTRICAS GERAIS =====
    total_products = Product.objects.count()
    total_active_products = Product.objects.filter(is_active=True).count()
    total_inactive_products = Product.objects.filter(is_active=False).count()

    # Pedidos efetivos (apenas os que geram receita real)
    effective_orders = Order.objects.effective()
    total_effective_sales = effective_orders.count()
    total_effective_revenue = effective_orders.total_revenue()

    effective_orders_last_7_days = Order.objects.effective().last_days(7)
    effective_orders_last_30_days = Order.objects.effective().last_days(30)

    # Vendas efetivas dos últimos períodos
    effective_sales_last_7_days = effective_orders_last_7_days.count()
    effective_revenue_last_7_days = effective_orders_last_7_days.total_revenue()

    effective_sales_last_30_days = effective_orders_last_30_days.count()
    effective_revenue_last_30_days = effective_orders_last_30_days.total_revenue()

    # Pedidos atrasados (globais)
    late_orders_count = Order.objects.late().count()

    # ===== DADOS PARA GRÁFICOS =====
    # CORREÇÃO: Usar queryset base para gráficos, não o já filtrado
    # Receita efetiva diária dos últimos 7 dias para gráfico
    effective_revenue_chart_7_days = Order.objects.effective().daily_revenue_last_days(
        7
    )

    # Receita efetiva diária dos últimos 30 dias para gráfico
    effective_revenue_chart_30_days = Order.objects.effective().daily_revenue_last_days(
        30
    )

    # Labels de datas para os gráficos
    chart_labels_7_days = get_date_labels(7)
    chart_labels_30_days = get_date_labels(30)

    return {
        # ===== MÉTRICAS DO DIA =====
        "orders_today": orders_today_count,
        "orders_pending_today": orders_pending_today,
        "orders_completed_today": orders_completed_today,
        "orders_cancelled_today": orders_cancelled_today,
        "orders_late_today": orders_late_today,
        "revenue_today": revenue_today,
        "revenue_paid_today": revenue_paid_today,
        "revenue_pending_today": revenue_pending_today,
        "revenue_cancelled_today": revenue_cancelled_today,
        # ===== MÉTRICAS GERAIS =====
        "total_products": total_products,
        "total_active_products": total_active_products,
        "total_inactive_products": total_inactive_products,
        "total_effective_sales": total_effective_sales,
        "total_effective_revenue": total_effective_revenue,
        "effective_sales_last_7_days": effective_sales_last_7_days,
        "effective_revenue_last_7_days": effective_revenue_last_7_days,
        "effective_sales_last_30_days": effective_sales_last_30_days,
        "effective_revenue_last_30_days": effective_revenue_last_30_days,
        "late_orders_count": late_orders_count,
        # ===== DADOS PARA GRÁFICOS =====
        "effective_revenue_chart_7_days": effective_revenue_chart_7_days,
        "effective_revenue_chart_30_days": effective_revenue_chart_30_days,
        "chart_labels_7_days": chart_labels_7_days,
        "chart_labels_30_days": chart_labels_30_days,
    }
