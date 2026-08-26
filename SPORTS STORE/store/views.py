import json
import logging

from django.conf import settings
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import Category, Product, Order, OrderItem
from .cart import Cart
from .forms import CheckoutForm
from . import payments

logger = logging.getLogger(__name__)


# ---------- Catálogo ----------

def home(request):
    categories = Category.objects.all()
    featured_products = Product.objects.filter(is_active=True)[:8]
    return render(request, 'store/home.html', {
        'categories': categories,
        'featured_products': featured_products,
    })


def product_list(request, category_slug=None):
    category = None
    categories = Category.objects.all()
    products = Product.objects.filter(is_active=True)

    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)

    query = request.GET.get('q')
    if query:
        products = products.filter(name__icontains=query)

    return render(request, 'store/product_list.html', {
        'category': category,
        'categories': categories,
        'products': products,
        'query': query or '',
    })


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    related_products = Product.objects.filter(
        category=product.category, is_active=True
    ).exclude(id=product.id)[:4]
    return render(request, 'store/product_detail.html', {
        'product': product,
        'related_products': related_products,
    })


# ---------- Carrito ----------

def cart_detail(request):
    cart = Cart(request)
    return render(request, 'store/cart_detail.html', {'cart': cart})


@require_POST
def cart_add(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id, is_active=True)
    quantity = int(request.POST.get('quantity', 1))
    cart.add(product=product, quantity=quantity)
    messages.success(request, f'"{product.name}" se agregó al carrito.')
    return redirect(request.POST.get('next', 'store:cart_detail'))


@require_POST
def cart_remove(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.remove(product)
    return redirect('store:cart_detail')


@require_POST
def cart_update(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    quantity = int(request.POST.get('quantity', 1))
    if quantity <= 0:
        cart.remove(product)
    else:
        cart.add(product=product, quantity=quantity, override_quantity=True)
    return redirect('store:cart_detail')


# ---------- Checkout ----------

def checkout(request):
    cart = Cart(request)
    if len(cart) == 0:
        messages.warning(request, 'Tu carrito está vacío.')
        return redirect('store:product_list')

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            order = Order.objects.create(
                customer_name=form.cleaned_data['customer_name'],
                email=form.cleaned_data['email'],
                phone=form.cleaned_data['phone'],
                address=form.cleaned_data['address'],
                city=form.cleaned_data['city'],
                postal_code=form.cleaned_data.get('postal_code', ''),
                notes=form.cleaned_data.get('notes', ''),
            )
            for item in cart:
                OrderItem.objects.create(
                    order=order,
                    product=item['product'],
                    product_name=item['product'].name,
                    unit_price=item['price'],
                    quantity=item['quantity'],
                )
            order.recalculate_total()

            try:
                preference = payments.create_preference(order)
            except RuntimeError as e:
                messages.error(request, str(e))
                return redirect('store:checkout')

            return redirect(preference['init_point'])
    else:
        form = CheckoutForm()

    return render(request, 'store/checkout.html', {'form': form, 'cart': cart})


def payment_success(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    cart = Cart(request)
    cart.clear()
    return render(request, 'store/payment_result.html', {
        'order': order, 'result': 'success'
    })


def payment_failure(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'store/payment_result.html', {
        'order': order, 'result': 'failure'
    })


def payment_pending(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    cart = Cart(request)
    cart.clear()
    return render(request, 'store/payment_result.html', {
        'order': order, 'result': 'pending'
    })


@csrf_exempt
def mercadopago_webhook(request):
    """
    Endpoint que recibe las notificaciones (IPN/webhook) de MercadoPago.
    Esta es la fuente de verdad sobre el estado real del pago: se consulta
    directamente a la API de MercadoPago (nunca se confía en datos que
    vengan solo del navegador del cliente).
    """
    if request.method != 'POST':
        return HttpResponse(status=405)

    try:
        payload = json.loads(request.body.decode('utf-8')) if request.body else {}
    except json.JSONDecodeError:
        payload = {}

    topic = request.GET.get('topic') or request.GET.get('type') or payload.get('type')
    payment_id = request.GET.get('id') or (payload.get('data') or {}).get('id')

    if topic == 'payment' and payment_id:
        try:
            payment_info = payments.get_payment_info(payment_id)
        except Exception as e:
            logger.exception('Error consultando pago de MercadoPago: %s', e)
            return HttpResponse(status=500)

        external_reference = payment_info.get('external_reference')
        status = payment_info.get('status')  # approved, pending, rejected, etc.

        if external_reference:
            try:
                order = Order.objects.get(id=external_reference)
            except Order.DoesNotExist:
                logger.warning('Webhook: Order %s no encontrada', external_reference)
                return HttpResponse(status=200)

            order.mp_payment_id = str(payment_id)
            order.mp_status_detail = payment_info.get('status_detail', '')

            if status == 'approved':
                order.status = 'paid'
            elif status == 'rejected':
                order.status = 'rejected'
            elif status == 'pending' or status == 'in_process':
                order.status = 'pending'

            order.save()
            logger.info('Pedido %s actualizado a estado %s', order.id, order.status)

    return HttpResponse(status=200)
