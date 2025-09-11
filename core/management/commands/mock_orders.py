"""
Django management command para criar pedidos mockados para demonstração.

Uso:
    python manage.py mock_orders                    # Criar pedidos de demo
    python manage.py mock_orders --cleanup          # Remover pedidos de demo
    python manage.py mock_orders --count 50         # Criar quantidade específica de pedidos
"""

import random
from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from checkout.models import Order, OrderItem
from products.models import Product


class Command(BaseCommand):
    help = "Cria pedidos mockados para demonstração do sistema"

    def add_arguments(self, parser):
        parser.add_argument(
            "--cleanup",
            action="store_true",
            help="Remove todos os pedidos de demonstração",
        )
        parser.add_argument(
            "--count",
            type=int,
            default=0,
            help="Número específico de pedidos para criar (0 = modo padrão)",
        )

    def handle(self, *args, **options):
        if options["cleanup"]:
            self.cleanup_demo_orders()
        else:
            count = options["count"]
            self.create_demo_orders(count if count > 0 else None)

    def cleanup_demo_orders(self):
        """Remove todos os pedidos de demonstração"""
        self.stdout.write(self.style.WARNING("🧹 Removendo pedidos de demonstração..."))

        try:
            deleted_count, deleted_details = Order.objects.filter(
                customer_name__contains="(DEMO"
            ).delete()

            self.stdout.write(
                self.style.SUCCESS(
                    f"✅ {deleted_count} pedidos de demonstração removidos"
                )
            )

            if deleted_details:
                self.stdout.write("📋 Detalhes:")
                for model, count in deleted_details.items():
                    if count > 0:
                        self.stdout.write(f"   - {model}: {count}")

        except Exception as e:
            raise CommandError(f"Erro ao remover pedidos: {e}")

    def create_demo_orders(self, specific_count=None):
        """Cria pedidos de demonstração com diferentes cenários"""

        self.stdout.write(
            self.style.HTTP_INFO("🚀 CRIANDO PEDIDOS MOCKADOS PARA DEMONSTRAÇÃO")
        )
        self.stdout.write("=" * 60)

        # Verificar se há produtos disponíveis
        products = list(Product.objects.filter(is_active=True))
        if not products:
            raise CommandError(
                "❌ Nenhum produto ativo encontrado! Crie produtos primeiro."
            )

        self.stdout.write(
            self.style.SUCCESS(f"✅ Encontrados {len(products)} produtos ativos:")
        )
        for i, product in enumerate(products):
            self.stdout.write(f"   {i + 1}. {product.name} - R$ {product.price}")

        try:
            with transaction.atomic():
                # ===== DADOS PARA DEMO =====
                customers = [
                    {
                        "name": "Maria Silva",
                        "phone": "11987654321",
                        "address": "Rua das Flores, 123 - Centro",
                    },
                    {
                        "name": "João Santos",
                        "phone": "11976543210",
                        "address": "Av. Principal, 456 - Jardim América",
                    },
                    {
                        "name": "Ana Costa",
                        "phone": "11965432109",
                        "address": "Rua do Comércio, 789 - Vila Nova",
                    },
                    {
                        "name": "Carlos Oliveira",
                        "phone": "11954321098",
                        "address": "Alameda dos Pássaros, 321 - Alto da Boa Vista",
                    },
                    {
                        "name": "Lucia Ferreira",
                        "phone": "11943210987",
                        "address": "Rua da Paz, 654 - Centro",
                    },
                    {
                        "name": "Pedro Almeida",
                        "phone": "11932109876",
                        "address": "Av. das Nações, 987 - Jardim Europa",
                    },
                    {
                        "name": "Sandra Lima",
                        "phone": "11921098765",
                        "address": "Rua Nova Esperança, 159 - Vila Progresso",
                    },
                    {
                        "name": "Roberto Dias",
                        "phone": "11910987654",
                        "address": "Alameda Central, 753 - Bela Vista",
                    },
                    {
                        "name": "Fernanda Rocha",
                        "phone": "11909876543",
                        "address": "Rua do Sol, 951 - Jardim Primavera",
                    },
                    {
                        "name": "Marcos Pereira",
                        "phone": "11898765432",
                        "address": "Av. da Liberdade, 357 - Centro Histórico",
                    },
                ]

                now = timezone.localtime()
                today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

                orders_created = 0
                total_revenue = Decimal("0.00")

                if specific_count:
                    # Modo específico: criar X pedidos distribuídos em diferentes datas
                    self.stdout.write(
                        f"\n📦 Criando {specific_count} pedidos distribuídos em diferentes datas..."
                    )

                    for i in range(specific_count):
                        customer = random.choice(customers)

                        # Status aleatório com peso para efetivos
                        status_weights = [
                            ("completed", "paid", 0.7),  # 70% efetivos
                            ("pending", "pending", 0.2),  # 20% pendentes
                            ("cancelled", "cancelled", 0.1),  # 10% cancelados
                        ]

                        rand = random.random()
                        cumulative = 0
                        for status, payment_status, weight in status_weights:
                            cumulative += weight
                            if rand <= cumulative:
                                selected_status = status
                                selected_payment_status = payment_status
                                break

                        # DISTRIBUIÇÃO INTELIGENTE: Mais pedidos concentrados hoje e dias recentes
                        # 50% dos pedidos hoje, 30% últimos 3 dias, 15% últimos 15 dias, 5% últimos 30 dias
                        date_rand = random.random()

                        if date_rand <= 0.5:  # 50% hoje - boa concentração no mesmo dia
                            days_ago = 0
                            hours_range = (
                                7,
                                21,
                            )  # Horário estendido para mais variedade
                        elif (
                            date_rand <= 0.8
                        ):  # 30% últimos 3 dias - concentração recente
                            days_ago = random.randint(1, 3)
                            hours_range = (8, 19)
                        elif (
                            date_rand <= 0.95
                        ):  # 15% últimos 15 dias - distribuição média
                            days_ago = random.randint(4, 15)
                            hours_range = (9, 18)
                        else:  # 5% últimos 30 dias - alguns históricos
                            days_ago = random.randint(16, 30)
                            hours_range = (9, 17)

                        # Calcular data específica com horários mais realistas
                        if days_ago == 0:
                            # Pedidos de hoje - horários com picos realistas
                            # Picos: 9h (café), 12h (almoço), 15h (tarde), 18h (fim do dia)
                            peak_hours = [9, 9, 12, 12, 12, 15, 15, 18, 18]
                            regular_hours = [7, 8, 10, 11, 13, 14, 16, 17, 19, 20, 21]

                            # 60% nos horários de pico, 40% nos regulares
                            if random.random() < 0.6:
                                selected_hour = random.choice(peak_hours)
                            else:
                                selected_hour = random.choice(regular_hours)

                            order_date = today_start + timedelta(
                                hours=selected_hour,
                                minutes=random.randint(0, 59),
                                seconds=random.randint(0, 59),
                            )
                        else:
                            # Pedidos de dias anteriores com horários variados
                            base_date = today_start - timedelta(days=days_ago)

                            # Horários mais concentrados no horário comercial para dias passados
                            if days_ago <= 3:
                                # Dias recentes: horários mais variados
                                hour_options = list(range(*hours_range)) + [
                                    10,
                                    14,
                                    16,
                                    18,
                                ]  # Reforçar alguns horários
                                selected_hour = random.choice(hour_options)
                            else:
                                # Dias mais antigos: horários mais concentrados
                                selected_hour = random.randint(*hours_range)

                            order_date = base_date + timedelta(
                                hours=selected_hour,
                                minutes=random.randint(0, 59),
                                seconds=random.randint(0, 59),
                            )

                        # Alguns pedidos atrasados (apenas se for hoje e pending)
                        is_late = False
                        if (
                            days_ago == 0
                            and selected_status == "pending"
                            and random.random() < 0.4
                        ):
                            # 40% dos pendentes de hoje serão atrasados (aumentei de 30% para 40%)
                            late_minutes = random.choice(
                                [25, 30, 45, 60, 90, 120, 150, 180]
                            )
                            order_date = now - timedelta(minutes=late_minutes)
                            is_late = True

                        customer_name = customer["name"]
                        if is_late:
                            customer_name += " ATRASADO"

                        order = Order.objects.create(
                            customer_name=f"{customer_name} (DEMO-{i + 1:03d})",
                            phone=customer["phone"],
                            address=customer["address"],
                            status=selected_status,
                            payment_status=selected_payment_status,
                            payment_method=random.choice(["pix", "dinheiro", "cartao"]),
                            created_at=order_date,
                        )

                        # Adicionar 1-3 produtos aleatórios
                        order_value = Decimal("0.00")
                        num_items = random.randint(1, 3)
                        for _ in range(num_items):
                            product = random.choice(products)
                            quantity = random.randint(1, 4)

                            OrderItem.objects.create(
                                order=order, product=product, quantity=quantity
                            )
                            order_value += product.price * quantity

                        if (
                            selected_status == "completed"
                            and selected_payment_status == "paid"
                        ):
                            total_revenue += order_value

                        orders_created += 1

                        # Progress indicator com info da data
                        if (
                            i + 1
                        ) % 5 == 0 or i < 5:  # Mostrar mais frequentemente no início
                            self.stdout.write(
                                f"   📊 {i + 1}/{specific_count} pedidos criados | Último: {order_date.strftime('%d/%m %H:%M')} ({days_ago} dias atrás)"
                            )

                        if (i + 1) % 10 == 0:
                            today_count = Order.objects.filter(
                                customer_name__contains="(DEMO",
                                created_at__date=today_start.date(),
                            ).count()
                            self.stdout.write(
                                f"   📊 {i + 1}/{specific_count} pedidos criados ({today_count} hoje)"
                            )

                    # Estatísticas finais de distribuição melhoradas
                    today_count = Order.objects.filter(
                        customer_name__contains="(DEMO",
                        created_at__date=today_start.date(),
                    ).count()

                    last_3_days_count = Order.objects.filter(
                        customer_name__contains="(DEMO",
                        created_at__gte=today_start - timedelta(days=3),
                    ).count()

                    last_7_days_count = Order.objects.filter(
                        customer_name__contains="(DEMO",
                        created_at__gte=today_start - timedelta(days=7),
                    ).count()

                    last_30_days_count = Order.objects.filter(
                        customer_name__contains="(DEMO",
                        created_at__gte=today_start - timedelta(days=30),
                    ).count()

                    # Estatísticas por status hoje
                    today_completed = Order.objects.filter(
                        customer_name__contains="(DEMO",
                        created_at__date=today_start.date(),
                        status="completed",
                    ).count()

                    today_pending = Order.objects.filter(
                        customer_name__contains="(DEMO",
                        created_at__date=today_start.date(),
                        status="pending",
                    ).count()

                    today_cancelled = Order.objects.filter(
                        customer_name__contains="(DEMO",
                        created_at__date=today_start.date(),
                        status="cancelled",
                    ).count()

                    self.stdout.write("\n📈 Distribuição criada:")
                    self.stdout.write(
                        f"   - HOJE: {today_count} pedidos (completados: {today_completed}, pendentes: {today_pending}, cancelados: {today_cancelled})"
                    )
                    self.stdout.write(
                        f"   - Últimos 3 dias: {last_3_days_count} pedidos"
                    )
                    self.stdout.write(
                        f"   - Últimos 7 dias: {last_7_days_count} pedidos"
                    )
                    self.stdout.write(
                        f"   - Últimos 30 dias: {last_30_days_count} pedidos"
                    )

                    # Porcentagem de concentração no dia atual
                    concentration_today = (
                        (today_count / specific_count * 100)
                        if specific_count > 0
                        else 0
                    )
                    self.stdout.write(
                        f"   - Concentração hoje: {concentration_today:.1f}% dos pedidos criados"
                    )

                else:
                    # Modo padrão: cenários específicos

                    # ===== PEDIDOS DE HOJE =====
                    self.stdout.write("\n📦 Criando pedidos de HOJE...")

                    # 1. Pedidos EFETIVOS de hoje (completed + paid) - AUMENTEI DE 8 PARA 12
                    for _ in range(12):
                        customer = random.choice(customers)

                        # Horários mais realistas com múltiplos picos
                        hour_weights = [
                            7,
                            8,
                            9,
                            9,
                            10,
                            10,
                            11,
                            12,
                            12,
                            12,
                            13,
                            14,
                            14,
                            15,
                            15,
                            16,
                            17,
                            17,
                            18,
                            18,
                            19,
                            20,
                        ]
                        selected_hour = random.choice(hour_weights)

                        order = Order.objects.create(
                            customer_name=f"{customer['name']} (DEMO)",
                            phone=customer["phone"],
                            address=customer["address"],
                            status="completed",
                            payment_status="paid",
                            payment_method=random.choice(["pix", "dinheiro", "cartao"]),
                            created_at=today_start
                            + timedelta(
                                hours=selected_hour,
                                minutes=random.randint(0, 59),
                                seconds=random.randint(0, 59),
                            ),
                        )

                        # Adicionar 1-3 produtos aleatórios
                        order_value = Decimal("0.00")
                        num_items = random.randint(1, 3)
                        for _ in range(num_items):
                            product = random.choice(products)
                            quantity = random.randint(1, 4)

                            OrderItem.objects.create(
                                order=order, product=product, quantity=quantity
                            )
                            order_value += product.price * quantity

                        total_revenue += order_value
                        orders_created += 1

                    # 2. Pedidos PENDENTES de hoje - AUMENTEI DE 4 PARA 6
                    for _ in range(6):
                        customer = random.choice(customers)

                        # Pedidos pendentes em horários mais recentes e variados
                        recent_hours = [12, 13, 14, 15, 16, 17, 18, 19, 20, 21]
                        selected_hour = random.choice(recent_hours)

                        order = Order.objects.create(
                            customer_name=f"{customer['name']} (DEMO)",
                            phone=customer["phone"],
                            address=customer["address"],
                            status="pending",
                            payment_status="pending",
                            payment_method=random.choice(["pix", "dinheiro", "cartao"]),
                            created_at=today_start
                            + timedelta(
                                hours=selected_hour,
                                minutes=random.randint(0, 59),
                                seconds=random.randint(0, 59),
                            ),
                        )

                        # Adicionar produtos
                        num_items = random.randint(1, 2)
                        for _ in range(num_items):
                            product = random.choice(products)
                            quantity = random.randint(1, 3)

                            OrderItem.objects.create(
                                order=order, product=product, quantity=quantity
                            )

                        orders_created += 1

                    # 3. Pedidos ATRASADOS - AUMENTEI DE 2 PARA 3 com mais variedade
                    late_times = [
                        25,
                        30,
                        45,
                        60,
                        75,
                        90,
                        120,
                        150,
                        180,
                        240,
                    ]  # mais opções de atraso
                    for _ in range(3):
                        customer = random.choice(customers)
                        minutes_ago = random.choice(late_times)

                        order = Order.objects.create(
                            customer_name=f"{customer['name']} (DEMO ATRASADO)",
                            phone=customer["phone"],
                            address=customer["address"],
                            status="pending",
                            payment_status="pending",
                            payment_method=random.choice(["pix", "dinheiro"]),
                            created_at=now
                            - timedelta(
                                minutes=minutes_ago, seconds=random.randint(0, 59)
                            ),
                        )

                        # Adicionar produto
                        product = random.choice(products)
                        OrderItem.objects.create(
                            order=order, product=product, quantity=random.randint(1, 2)
                        )

                        orders_created += 1

                    # 4. Alguns pedidos CANCELADOS de hoje - horários variados
                    for _ in range(3):  # aumentei de 2 para 3
                        customer = random.choice(customers)

                        # Cancelados podem ser de qualquer horário
                        cancel_hours = [8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19]
                        selected_hour = random.choice(cancel_hours)

                        order = Order.objects.create(
                            customer_name=f"{customer['name']} (DEMO)",
                            phone=customer["phone"],
                            address=customer["address"],
                            status="cancelled",
                            payment_status="cancelled",
                            payment_method=random.choice(["pix", "cartao"]),
                            created_at=today_start
                            + timedelta(
                                hours=selected_hour,
                                minutes=random.randint(0, 59),
                                seconds=random.randint(0, 59),
                            ),
                        )

                        # Adicionar produto
                        product = random.choice(products)
                        OrderItem.objects.create(
                            order=order, product=product, quantity=random.randint(1, 2)
                        )

                        orders_created += 1

                    self.stdout.write(self.style.SUCCESS("✅ Pedidos de hoje criados"))

                    # ===== PEDIDOS DOS ÚLTIMOS DIAS =====
                    self.stdout.write("\n📊 Criando pedidos dos ÚLTIMOS DIAS...")

                    # Pedidos dos últimos 3 dias (mais concentração nos dias recentes)
                    for day in range(1, 4):
                        target_date = today_start - timedelta(days=day)

                        # MAIS pedidos nos dias mais recentes: 4-7 pedidos
                        num_orders_day = random.randint(4, 7)
                        for _ in range(num_orders_day):
                            customer = random.choice(customers)

                            # Horários variados com picos
                            hour_options = [
                                8,
                                9,
                                10,
                                10,
                                11,
                                12,
                                12,
                                13,
                                14,
                                14,
                                15,
                                16,
                                17,
                                17,
                                18,
                                19,
                            ]
                            selected_hour = random.choice(hour_options)

                            # 85% efetivos, 10% pendentes, 5% cancelados para dias recentes
                            status_rand = random.random()
                            if status_rand <= 0.85:
                                status, payment_status = "completed", "paid"
                            elif status_rand <= 0.95:
                                status, payment_status = "pending", "pending"
                            else:
                                status, payment_status = "cancelled", "cancelled"

                            order = Order.objects.create(
                                customer_name=f"{customer['name']} (DEMO)",
                                phone=customer["phone"],
                                address=customer["address"],
                                status=status,
                                payment_status=payment_status,
                                payment_method=random.choice(
                                    ["pix", "dinheiro", "cartao"]
                                ),
                                created_at=target_date
                                + timedelta(
                                    hours=selected_hour,
                                    minutes=random.randint(0, 59),
                                    seconds=random.randint(0, 59),
                                ),
                            )

                            # Adicionar produtos
                            order_value = Decimal("0.00")
                            num_items = random.randint(1, 3)
                            for _ in range(num_items):
                                product = random.choice(products)
                                quantity = random.randint(1, 3)

                                OrderItem.objects.create(
                                    order=order, product=product, quantity=quantity
                                )
                                order_value += product.price * quantity

                            if status == "completed" and payment_status == "paid":
                                total_revenue += order_value
                            orders_created += 1

                        self.stdout.write(f"   Dia -{day}: {num_orders_day} pedidos")

                    # Pedidos dos dias 4-7 (quantidade média)
                    for day in range(4, 8):
                        target_date = today_start - timedelta(days=day)

                        # 2-4 pedidos efetivos por dia
                        num_orders_day = random.randint(2, 4)
                        for _ in range(num_orders_day):
                            customer = random.choice(customers)

                            order = Order.objects.create(
                                customer_name=f"{customer['name']} (DEMO)",
                                phone=customer["phone"],
                                address=customer["address"],
                                status="completed",
                                payment_status="paid",
                                payment_method=random.choice(
                                    ["pix", "dinheiro", "cartao"]
                                ),
                                created_at=target_date
                                + timedelta(
                                    hours=random.randint(8, 18),
                                    minutes=random.randint(0, 59),
                                    seconds=random.randint(0, 59),
                                ),
                            )

                            # Adicionar produtos
                            order_value = Decimal("0.00")
                            num_items = random.randint(1, 3)
                            for _ in range(num_items):
                                product = random.choice(products)
                                quantity = random.randint(1, 3)

                                OrderItem.objects.create(
                                    order=order, product=product, quantity=quantity
                                )
                                order_value += product.price * quantity

                            total_revenue += order_value
                            orders_created += 1

                        self.stdout.write(f"   Dia -{day}: {num_orders_day} pedidos")

                    # ===== PEDIDOS DOS ÚLTIMOS 30 DIAS =====
                    self.stdout.write("\n📈 Criando pedidos dos ÚLTIMOS 30 DIAS...")

                    # Pedidos dos dias 8-30 (distribuição histórica)
                    for day in range(8, 31):
                        target_date = today_start - timedelta(days=day)

                        # Variar quantidade: mais no início do período, menos no final
                        if day <= 15:
                            num_orders_day = random.randint(1, 3)  # Período recente
                        else:
                            num_orders_day = random.randint(0, 2)  # Período mais antigo

                        for _ in range(num_orders_day):
                            customer = random.choice(customers)

                            # Horários mais concentrados no período histórico
                            business_hours = [9, 10, 11, 12, 13, 14, 15, 16, 17]
                            selected_hour = random.choice(business_hours)

                            order = Order.objects.create(
                                customer_name=f"{customer['name']} (DEMO)",
                                phone=customer["phone"],
                                address=customer["address"],
                                status="completed",
                                payment_status="paid",
                                payment_method=random.choice(
                                    ["pix", "dinheiro", "cartao"]
                                ),
                                created_at=target_date
                                + timedelta(
                                    hours=selected_hour,
                                    minutes=random.randint(0, 59),
                                    seconds=random.randint(0, 59),
                                ),
                            )

                            # Adicionar produtos (quantidade menor para pedidos históricos)
                            order_value = Decimal("0.00")
                            num_items = random.randint(1, 2)
                            for _ in range(num_items):
                                product = random.choice(products)
                                quantity = random.randint(1, 2)

                                OrderItem.objects.create(
                                    order=order, product=product, quantity=quantity
                                )
                                order_value += product.price * quantity

                            total_revenue += order_value
                            orders_created += 1

                        # Mostrar progresso a cada 5 dias
                        if day % 5 == 0:
                            self.stdout.write(
                                f"   Dia -{day}: processado ({num_orders_day} pedidos)"
                            )

                    self.stdout.write(
                        self.style.SUCCESS("✅ Pedidos dos últimos 30 dias criados")
                    )

                # ===== RESUMO =====
                self.stdout.write("\n" + "=" * 60)
                self.stdout.write(
                    self.style.SUCCESS("🎉 PEDIDOS MOCKADOS CRIADOS COM SUCESSO!")
                )
                self.stdout.write(f"📦 Total de pedidos: {orders_created}")
                self.stdout.write(f"💰 Receita total estimada: R$ {total_revenue:.2f}")

                # Estatísticas finais para todos os modos
                final_today_count = Order.objects.filter(
                    customer_name__contains="(DEMO", created_at__date=today_start.date()
                ).count()

                final_total_count = Order.objects.filter(
                    customer_name__contains="(DEMO"
                ).count()

                concentration_percentage = (
                    (final_today_count / final_total_count * 100)
                    if final_total_count > 0
                    else 0
                )

                self.stdout.write(
                    f"📊 Concentração no dia atual: {final_today_count}/{final_total_count} pedidos ({concentration_percentage:.1f}%)"
                )
                self.stdout.write("\n📊 CARACTERÍSTICAS DA DISTRIBUIÇÃO:")
                self.stdout.write("   ✅ Maior concentração de pedidos no dia atual")
                self.stdout.write("   ✅ Horários realistas com picos de demanda")
                self.stdout.write("   ✅ Distribuição variada nos últimos 30 dias")
                self.stdout.write("   ✅ Pedidos atrasados para demonstração")
                self.stdout.write("   ✅ Diferentes status de pagamento")
                self.stdout.write("\n📊 VISUALIZAÇÃO DISPONÍVEL:")
                self.stdout.write("   - Dashboard com métricas em tempo real")
                self.stdout.write("   - Gráficos de tendência de vendas")
                self.stdout.write("   - Pedidos atrasados destacados")
                self.stdout.write("   - Receitas por status de pagamento")
                self.stdout.write("\n🌐 Acesse: http://localhost:8000/dashboard/")
                self.stdout.write("=" * 60)

        except Exception as e:
            raise CommandError(f"Erro ao criar pedidos: {e}")
