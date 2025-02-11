from django.contrib.auth.management.commands.createsuperuser import Command as BaseCommand
from django.core.management import CommandError

class Command(BaseCommand):
    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument('--birth_date', type=str, help='User birth date (YYYY-MM-DD)')
        parser.add_argument('--country', type=str, help='User country')
        parser.add_argument('--address', type=str, help='User address')
        parser.add_argument('--postal_code', type=str, help='User postal code')

    def handle(self, *args, **options):
        birth_date = options.get('birth_date')
        country = options.get('country')
        address = options.get('address')
        postal_code = options.get('postal_code')

        if not birth_date or not country or not address or not postal_code:
            raise CommandError('You must provide birth_date, country, address, and postal_code.')

        options['extra_fields'] = {
            'birth_date': birth_date,
            'country': country,
            'address': address,
            'postal_code': postal_code,
        }

        super().handle(*args, **options)
