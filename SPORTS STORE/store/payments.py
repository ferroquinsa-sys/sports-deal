"""
Integración con MercadoPago usando Checkout Pro.

Flujo:
1. Se crea el Order en la base de datos con estado 'pending'.
2. Se crea una "preferencia de pago" en MercadoPago con los ítems del pedido.
3. Se redirige al cliente al 'init_point' que devuelve MercadoPago (checkout alojado por ellos).
4. El cliente paga en MercadoPago y vuelve a nuestro sitio (back_urls).
5. MercadoPago también notifica el resultado real del pago vía webhook (notification_url),
   que es la fuente de verdad para confirmar el pago (más confiable que el back_url,
   porque el webhook llega aunque el usuario cierre el navegador).
"""

import mercadopago
from django.conf import settings


def get_sdk():
    if not settings.MERCADOPAGO_ACCESS_TOKEN:
        raise RuntimeError(
            'Falta configurar MERCADOPAGO_ACCESS_TOKEN en el archivo .env. '
            'Consultá el README para obtener tus credenciales.'
        )
    return mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN)


def create_preference(order):
    """Crea una preferencia de pago en MercadoPago para un Order dado."""
    sdk = get_sdk()

    items = [
        {
            'title': item.product_name[:250],
            'quantity': item.quantity,
            'unit_price': float(item.unit_price),
            'currency_id': 'ARS',
        }
        for item in order.items.all()
    ]

    preference_data = {
        'items': items,
        'payer': {
            'name': order.customer_name,
            'email': order.email,
        },
        'back_urls': {
            'success': f'{settings.SITE_URL}/pago/exito/{order.id}/',
            'failure': f'{settings.SITE_URL}/pago/error/{order.id}/',
            'pending': f'{settings.SITE_URL}/pago/pendiente/{order.id}/',
        },
        'auto_return': 'approved',
        'external_reference': str(order.id),
        'notification_url': f'{settings.SITE_URL}/pago/webhook/mercadopago/',
        'statement_descriptor': 'SPORTSDEAL',
    }

    response = sdk.preference().create(preference_data)
    preference = response['response']

    order.mp_preference_id = preference.get('id', '')
    order.save(update_fields=['mp_preference_id'])

    return preference


def get_payment_info(payment_id):
    """Consulta el estado real de un pago en MercadoPago (usado en el webhook)."""
    sdk = get_sdk()
    response = sdk.payment().get(payment_id)
    return response['response']
