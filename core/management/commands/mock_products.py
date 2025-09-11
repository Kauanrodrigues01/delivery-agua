from django.core.management.base import BaseCommand, CommandError
import random

from products.models import Product

class Command(BaseCommand):
    help = 'Create mock products for testing purposes'
    
    def add_arguments(self, parser):
        parser.add_argument('--count', type=int, default=20, help='Number of mock products to create')
        return super().add_arguments(parser)

    def handle(self, *args, **kwargs):
        count = kwargs.get('count', 20)
        try:
            for i in range(count):
                Product.objects.create(
                    name=f'Produto Mock {i+1}',
                    description='Descrição do produto mock.',
                    price=random.uniform(5.0, 100.0),
                    is_active=True
                )
            self.stdout.write(self.style.SUCCESS(f'Successfully created {count} mock products.'))
        except Exception as e:
            raise CommandError(f'Error creating mock products: {e}')
