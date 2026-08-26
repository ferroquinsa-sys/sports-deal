from django.urls import path
from . import views

app_name = 'store'

urlpatterns = [
    path('', views.home, name='home'),
    path('productos/', views.product_list, name='product_list'),
    path('categoria/<slug:category_slug>/', views.product_list, name='product_list_by_category'),
    path('producto/<slug:slug>/', views.product_detail, name='product_detail'),

    path('carrito/', views.cart_detail, name='cart_detail'),
    path('carrito/agregar/<int:product_id>/', views.cart_add, name='cart_add'),
    path('carrito/eliminar/<int:product_id>/', views.cart_remove, name='cart_remove'),
    path('carrito/actualizar/<int:product_id>/', views.cart_update, name='cart_update'),

    path('checkout/', views.checkout, name='checkout'),

    path('pago/exito/<int:order_id>/', views.payment_success, name='payment_success'),
    path('pago/error/<int:order_id>/', views.payment_failure, name='payment_failure'),
    path('pago/pendiente/<int:order_id>/', views.payment_pending, name='payment_pending'),
    path('pago/webhook/mercadopago/', views.mercadopago_webhook, name='mercadopago_webhook'),
]
