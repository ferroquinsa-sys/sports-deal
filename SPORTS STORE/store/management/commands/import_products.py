import csv
from decimal import Decimal, InvalidOperation

from django.core.management.base import BaseCommand, CommandError
from store.models import Category, Product


class Command(BaseCommand):
    help = (
        'Importa productos propios desde un archivo CSV. '
        'Columnas esperadas: name,description,price,stock,category\n'
        'Ejemplo de uso: python manage.py import_products productos.csv'
    )

    def add_arguments(self, parser):
        parser.add_argument('csv_path', type=str, help='Ruta al archivo CSV de productos')

    def handle(self, *args, **options):
        path = options['csv_path']
        created, updated, errors = 0, 0, 0

        try:
            f = open(path, newline='', encoding='utf-8')
        except FileNotFoundError:
            raise CommandError(f'No se encontró el archivo: {path}')

        with f:
            reader = csv.DictReader(f)
            required_cols = {'name', 'price'}
            if not required_cols.issubset(set(reader.fieldnames or [])):
                raise CommandError(
                    f'El CSV debe tener al menos las columnas: {", ".join(required_cols)}. '
                    f'Columnas encontradas: {reader.fieldnames}'
                )

            for i, row in enumerate(reader, start=2):
                name = (row.get('name') or '').strip()
                if not name:
                    self.stderr.write(f'Fila {i}: sin nombre, se omite.')
                    errors += 1
                    continue

                try:
                    price = Decimal(str(row.get('price', '0')).strip())
                except (InvalidOperation, ValueError):
                    self.stderr.write(f'Fila {i}: precio inválido para "{name}", se omite.')
                    errors += 1
                    continue

                stock = row.get('stock', '0').strip() or '0'
                try:
                    stock = int(stock)
                except ValueError:
                    stock = 0

                category = None
                category_name = (row.get('category') or '').strip()
                if category_name:
                    category, _ = Category.objects.get_or_create(name=category_name)

                product, was_created = Product.objects.update_or_create(
                    name=name,
                    defaults={
                        'description': (row.get('description') or '').strip(),
                        'price': price,
                        'stock': stock,
                        'category': category,
                        'is_active': True,
                    }
                )
                if was_created:
                    created += 1
                else:
                    updated += 1

        self.stdout.write(self.style.SUCCESS(
            f'Importación finalizada. Creados: {created} | Actualizados: {updated} | Con errores: {errors}'
        ))
        self.stdout.write(
            'Recordá subir las imágenes de cada producto desde el Back Office (/admin/) '
            'ya que el CSV no incluye archivos de imagen.'
        )
