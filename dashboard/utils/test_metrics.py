"""
Teste abrangente para validar os cálculos das métricas do dashboard.
Este arquivo cria cenários complexos de pedidos com diferentes status e valores
para garantir que todos os cálculos estão corretos.

Execute com: python manage.py shell < dashboard/utils/test_metrics.py
Ou: python manage.py test dashboard.utils.test_metrics
"""

from datetime import timedelta
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from checkout.models import Order, OrderItem
from dashboard.utils.metrics import calculate_metrics
from products.models import Product


class MetricsTestSuite:
    """Suite de testes para validar métricas do dashboard"""

    def __init__(self):
        self.test_data = {}
        self.products = []

    def setup_test_products(self):
        """Cria produtos de teste"""
        print("🔧 Criando produtos de teste...")

        # Limpar produtos existentes de teste
        Product.objects.filter(name__startswith="TESTE_").delete()

        products_data = [
            {"name": "TESTE_Água 20L", "price": Decimal("15.00")},
            {"name": "TESTE_Água 10L", "price": Decimal("8.50")},
            {"name": "TESTE_Galão Vazio", "price": Decimal("25.00")},
            {"name": "TESTE_Kit Bomba", "price": Decimal("45.00")},
        ]

        for product_data in products_data:
            product = Product.objects.create(
                name=product_data["name"],
                description=f"Produto de teste - {product_data['name']}",
                price=product_data["price"],
                image="test.jpg",
                is_active=True,
            )
            self.products.append(product)

        print(f"✅ {len(self.products)} produtos criados")

    def cleanup_test_data(self):
        """Remove dados de teste"""
        # print("🧹 Limpando dados de teste...")
        # Order.objects.filter(customer_name__startswith='TESTE_').delete()
        # Product.objects.filter(name__startswith='TESTE_').delete()
        # print("✅ Dados de teste removidos")
        ...

    def create_order(
        self,
        customer_name,
        phone,
        address,
        status,
        payment_status,
        payment_method="pix",
        cash_value=None,
        items=None,
        created_at=None,
    ):
        """
        Cria um pedido com os parâmetros especificados

        Args:
            items: Lista de dicts com 'product_index' e 'quantity'
            created_at: Data específica para o pedido (None = agora)
        """
        if items is None:
            items = [{"product_index": 0, "quantity": 1}]

        # Criar o pedido
        order = Order.objects.create(
            customer_name=customer_name,
            phone=phone,
            address=address,
            status=status,
            payment_status=payment_status,
            payment_method=payment_method,
            cash_value=cash_value,
        )

        # Se uma data específica foi fornecida, atualizar
        if created_at:
            order.created_at = created_at
            order.save()

        # Criar itens do pedido
        total_value = Decimal("0.00")
        for item_data in items:
            product = self.products[item_data["product_index"]]
            quantity = item_data["quantity"]

            OrderItem.objects.create(order=order, product=product, quantity=quantity)

            total_value += product.price * quantity

        return order, total_value

    def create_test_scenario(self):
        """Cria cenário complexo de teste com pedidos variados"""
        print("📊 Criando cenário de teste...")

        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        # ===== PEDIDOS DE HOJE =====

        # 1. Pedidos EFETIVOS de hoje (completed + paid)
        order1, value1 = self.create_order(
            "TESTE_Cliente_1",
            "11999999001",
            "Rua A, 123",
            status="completed",
            payment_status="paid",
            items=[
                {"product_index": 0, "quantity": 2},  # 2x Água 20L = 30.00
                {"product_index": 1, "quantity": 1},  # 1x Água 10L = 8.50
            ],
            created_at=today_start + timedelta(hours=8),
        )

        order2, value2 = self.create_order(
            "TESTE_Cliente_2",
            "11999999002",
            "Rua B, 456",
            status="completed",
            payment_status="paid",
            items=[
                {"product_index": 2, "quantity": 1},  # 1x Galão = 25.00
            ],
            created_at=today_start + timedelta(hours=10),
        )

        # 2. Pedidos PENDENTES de hoje (pending + pending)
        order3, value3 = self.create_order(
            "TESTE_Cliente_3",
            "11999999003",
            "Rua C, 789",
            status="pending",
            payment_status="pending",
            items=[
                {"product_index": 0, "quantity": 1},  # 1x Água 20L = 15.00
            ],
            created_at=today_start + timedelta(hours=12),
        )

        # 3. Pedidos PAGOS mas não concluídos (pending + paid) - não são efetivos
        order4, value4 = self.create_order(
            "TESTE_Cliente_4",
            "11999999004",
            "Rua D, 101",
            status="pending",
            payment_status="paid",
            items=[
                {"product_index": 1, "quantity": 2},  # 2x Água 10L = 17.00
            ],
            created_at=today_start + timedelta(hours=14),
        )

        # 4. Pedidos CANCELADOS (cancelled + cancelled)
        order5, value5 = self.create_order(
            "TESTE_Cliente_5",
            "11999999005",
            "Rua E, 202",
            status="cancelled",
            payment_status="cancelled",
            items=[
                {"product_index": 3, "quantity": 1},  # 1x Kit Bomba = 45.00
            ],
            created_at=today_start + timedelta(hours=16),
        )

        # 5. Pedido ATRASADO (pending há mais de 25 min)
        order6, value6 = self.create_order(
            "TESTE_Cliente_6",
            "11999999006",
            "Rua F, 303",
            status="pending",
            payment_status="pending",
            items=[
                {"product_index": 0, "quantity": 1},  # 1x Água 20L = 15.00
            ],
            created_at=now - timedelta(minutes=30),  # 30 min atrás = atrasado
        )

        # ===== PEDIDOS DOS ÚLTIMOS 7 DIAS (excluindo hoje) =====

        # Pedido efetivo de 3 dias atrás
        order7, value7 = self.create_order(
            "TESTE_Cliente_7",
            "11999999007",
            "Rua G, 404",
            status="completed",
            payment_status="paid",
            items=[
                {"product_index": 0, "quantity": 3},  # 3x Água 20L = 45.00
                {"product_index": 2, "quantity": 1},  # 1x Galão = 25.00
            ],
            created_at=today_start - timedelta(days=3, hours=10),
        )

        # Pedido efetivo de 5 dias atrás
        order8, value8 = self.create_order(
            "TESTE_Cliente_8",
            "11999999008",
            "Rua H, 505",
            status="completed",
            payment_status="paid",
            items=[
                {"product_index": 1, "quantity": 4},  # 4x Água 10L = 34.00
            ],
            created_at=today_start - timedelta(days=5, hours=15),
        )

        # ===== PEDIDOS DOS ÚLTIMOS 30 DIAS (excluindo os já criados) =====

        # Pedido efetivo de 15 dias atrás
        order9, value9 = self.create_order(
            "TESTE_Cliente_9",
            "11999999009",
            "Rua I, 606",
            status="completed",
            payment_status="paid",
            items=[
                {"product_index": 3, "quantity": 2},  # 2x Kit Bomba = 90.00
            ],
            created_at=today_start - timedelta(days=15, hours=9),
        )

        # Pedido efetivo de 25 dias atrás
        order10, value10 = self.create_order(
            "TESTE_Cliente_10",
            "11999999010",
            "Rua J, 707",
            status="completed",
            payment_status="paid",
            items=[
                {"product_index": 0, "quantity": 1},  # 1x Água 20L = 15.00
                {"product_index": 1, "quantity": 1},  # 1x Água 10L = 8.50
                {"product_index": 2, "quantity": 1},  # 1x Galão = 25.00
            ],
            created_at=today_start - timedelta(days=25, hours=11),
        )

        # ===== PEDIDOS ANTIGOS (fora dos últimos 30 dias) =====

        # Pedido efetivo de 35 dias atrás (não deve aparecer nas métricas de 30 dias)
        order11, value11 = self.create_order(
            "TESTE_Cliente_11",
            "11999999011",
            "Rua K, 808",
            status="completed",
            payment_status="paid",
            items=[
                {"product_index": 0, "quantity": 5},  # 5x Água 20L = 75.00
            ],
            created_at=today_start - timedelta(days=35, hours=14),
        )

        # ===== ARMAZENAR VALORES ESPERADOS =====

        self.test_data = {
            # MÉTRICAS DO DIA
            "expected_orders_today": 6,  # orders 1-6
            "expected_orders_pending_today": 3,  # orders 3, 4, 6
            "expected_orders_completed_today": 2,  # orders 1, 2
            "expected_orders_cancelled_today": 1,  # order 5
            "expected_orders_late_today": 1,  # order 6 (30 min atrás)
            # RECEITAS DO DIA
            "expected_revenue_paid_today": float(
                value1 + value2 + value4
            ),  # orders 1, 2, 4
            "expected_revenue_pending_today": float(value3 + value6),  # orders 3, 6
            "expected_revenue_cancelled_today": float(value5),  # order 5
            "expected_revenue_today": float(
                value1 + value2 + value3 + value4 + value6
            ),  # exclui cancelado
            # MÉTRICAS GERAIS
            "expected_total_effective_sales": 6,  # orders 1, 2, 7, 8, 9, 10, 11
            "expected_total_effective_revenue": float(
                value1 + value2 + value7 + value8 + value9 + value10 + value11
            ),
            # ÚLTIMOS 7 DIAS (inclui hoje)
            "expected_effective_sales_last_7_days": 4,  # orders 1, 2, 7, 8
            "expected_effective_revenue_last_7_days": float(
                value1 + value2 + value7 + value8
            ),
            # ÚLTIMOS 30 DIAS (inclui hoje)
            "expected_effective_sales_last_30_days": 6,  # orders 1, 2, 7, 8, 9, 10
            "expected_effective_revenue_last_30_days": float(
                value1 + value2 + value7 + value8 + value9 + value10
            ),
            # PEDIDOS ATRASADOS GLOBAIS
            "expected_late_orders_count": 1,  # order 6 apenas
        }

        print(
            f"✅ Cenário criado: {Order.objects.filter(customer_name__startswith='TESTE_').count()} pedidos"
        )

        # Debug: Mostrar valores esperados
        print("\n📋 VALORES ESPERADOS:")
        for key, value in self.test_data.items():
            print(f"  {key}: {value}")

    def validate_metrics(self):
        """Valida se as métricas calculadas batem com os valores esperados"""
        print("\n🔍 Calculando métricas...")

        metrics = calculate_metrics()

        print("\n✅ VALIDAÇÃO DOS RESULTADOS:")

        errors = []

        # Validar cada métrica
        validations = [
            ("orders_today", "expected_orders_today"),
            ("orders_pending_today", "expected_orders_pending_today"),
            ("orders_completed_today", "expected_orders_completed_today"),
            ("orders_cancelled_today", "expected_orders_cancelled_today"),
            ("orders_late_today", "expected_orders_late_today"),
            ("revenue_paid_today", "expected_revenue_paid_today"),
            ("revenue_pending_today", "expected_revenue_pending_today"),
            ("revenue_cancelled_today", "expected_revenue_cancelled_today"),
            ("revenue_today", "expected_revenue_today"),
            ("total_effective_sales", "expected_total_effective_sales"),
            ("total_effective_revenue", "expected_total_effective_revenue"),
            ("effective_sales_last_7_days", "expected_effective_sales_last_7_days"),
            ("effective_revenue_last_7_days", "expected_effective_revenue_last_7_days"),
            ("effective_sales_last_30_days", "expected_effective_sales_last_30_days"),
            (
                "effective_revenue_last_30_days",
                "expected_effective_revenue_last_30_days",
            ),
            ("late_orders_count", "expected_late_orders_count"),
        ]

        for metric_key, expected_key in validations:
            actual = metrics[metric_key]
            expected = self.test_data[expected_key]

            # Para valores monetários, comparar com tolerância de 0.01
            if isinstance(expected, float):
                is_correct = abs(actual - expected) < 0.01
            else:
                is_correct = actual == expected

            status = "✅" if is_correct else "❌"
            print(f"{status} {metric_key}: {actual} (esperado: {expected})")

            if not is_correct:
                errors.append(f"{metric_key}: obtido {actual}, esperado {expected}")

        return errors

    def run_full_test(self):
        """Executa o teste completo"""
        print("🚀 INICIANDO TESTE COMPLETO DAS MÉTRICAS\n")

        try:
            with transaction.atomic():
                # Setup
                self.cleanup_test_data()
                self.setup_test_products()
                self.create_test_scenario()

                # Validação
                errors = self.validate_metrics()

                if errors:
                    print(f"\n❌ TESTE FALHOU! {len(errors)} erros encontrados:")
                    for error in errors:
                        print(f"  - {error}")
                    return False
                else:
                    print("\n🎉 TESTE PASSOU! Todas as métricas estão corretas!")
                    return True

        except Exception as e:
            print(f"\n💥 ERRO DURANTE O TESTE: {e}")
            import traceback

            traceback.print_exc()
            return False
        finally:
            # Cleanup
            print("\n🧹 Limpando dados de teste...")
            self.cleanup_test_data()


def run_metrics_test():
    """Executa o teste das métricas - função standalone para o shell"""
    test_suite = MetricsTestSuite()
    success = test_suite.run_full_test()

    if success:
        print("\n✅ SISTEMA DE MÉTRICAS VALIDADO COM SUCESSO!")
    else:
        print("\n❌ SISTEMA DE MÉTRICAS CONTÉM ERROS!")

    print("\n" + "=" * 60)
    return success


# Para uso direto no shell Django
if __name__ == "__main__":
    # Se executado diretamente, chama a função de teste
    run_metrics_test()
