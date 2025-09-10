from datetime import timedelta
from django.utils.timezone import now
from django.db.models import Sum

from checkout.models import Order
from products.models import Product


def get_date_labels(days):
    """
    Gera labels de datas para gráficos
    Formato: ['01/09', '02/09', '03/09', ...]
    """
    labels = []
    for i in range(days):
        target_date = (now() - timedelta(days=days-1-i)).date()
        labels.append(target_date.strftime('%d/%m'))
    return labels


# Função para calcular todas as métricas
def calculate_metrics():
    # ===== MÉTRICAS DO DIA =====
    orders_today = Order.objects.today()
    
    # Quantidade de pedidos por status hoje
    orders_today_count = orders_today.count()
    orders_pending_today = orders_today.pending().count()
    orders_completed_today = orders_today.completed().count()
    orders_cancelled_today = orders_today.cancelled().count()
    orders_late_today = orders_today.late().count()
    
    # Receitas do dia por status de pagamento
    revenue_paid_today = orders_today.paid().total_revenue()
    revenue_pending_today = orders_today.payment_pending().total_revenue()
    revenue_cancelled_today = orders_today.payment_cancelled().total_revenue()
    revenue_today = revenue_paid_today + revenue_pending_today + revenue_cancelled_today
    
    # ===== MÉTRICAS GERAIS =====
    total_products = Product.objects.count()
    total_active_products = Product.objects.filter(is_active=True).count()
    total_inactive_products = Product.objects.filter(is_active=False).count()

    # Pedidos efetivos (apenas os que geram receita real)
    effective_orders = Order.objects.effective()
    total_effective_sales = effective_orders.count()
    total_effective_revenue = effective_orders.total_revenue()
    
    # Vendas efetivas dos últimos períodos
    effective_sales_last_7_days = effective_orders.last_days(7).count()
    effective_revenue_last_7_days = effective_orders.last_days(7).total_revenue()
    
    effective_sales_last_30_days = effective_orders.last_days(30).count()
    effective_revenue_last_30_days = effective_orders.last_days(30).total_revenue()

    # Pedidos atrasados (globais)
    late_orders_count = Order.objects.late().count()

    # ===== DADOS PARA GRÁFICOS =====
    # Receita efetiva diária dos últimos 7 dias para gráfico
    effective_revenue_chart_7_days = effective_orders.daily_revenue_last_days(7)
    
    # Receita efetiva diária dos últimos 30 dias para gráfico
    effective_revenue_chart_30_days = effective_orders.daily_revenue_last_days(30)
    
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
