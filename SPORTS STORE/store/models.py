from django.db import models
from django.utils.text import slugify
from django.urls import reverse
from decimal import Decimal


class Category(models.Model):
    name = models.CharField('Nombre', max_length=100)
    slug = models.SlugField(max_length=110, unique=True, blank=True)

    class Meta:
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True,
                                  related_name='products', verbose_name='Categoría')
    name = models.CharField('Nombre', max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    description = models.TextField('Descripción', blank=True)
    price = models.DecimalField('Precio', max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField('Stock', default=0)
    image = models.ImageField('Imagen', upload_to='products/', blank=True, null=True)
    is_active = models.BooleanField('Activo (visible en la tienda)', default=True)
    created_at = models.DateTimeField('Creado', auto_now_add=True)
    updated_at = models.DateTimeField('Actualizado', auto_now=True)

    class Meta:
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            i = 1
            while Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                i += 1
                slug = f'{base_slug}-{i}'
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('store:product_detail', args=[self.slug])

    @property
    def in_stock(self):
        return self.stock > 0


ORDER_STATUS_CHOICES = [
    ('pending', 'Pendiente de pago'),
    ('paid', 'Pagado'),
    ('shipped', 'Enviado'),
    ('cancelled', 'Cancelado'),
    ('rejected', 'Pago rechazado'),
]


class Order(models.Model):
    # Datos del cliente (checkout como invitado)
    customer_name = models.CharField('Nombre y apellido', max_length=200)
    email = models.EmailField('Email')
    phone = models.CharField('Teléfono', max_length=30)
    address = models.CharField('Dirección', max_length=255)
    city = models.CharField('Ciudad', max_length=100)
    postal_code = models.CharField('Código postal', max_length=20, blank=True)
    notes = models.TextField('Notas', blank=True)

    status = models.CharField('Estado', max_length=20, choices=ORDER_STATUS_CHOICES, default='pending')
    total = models.DecimalField('Total', max_digits=10, decimal_places=2, default=Decimal('0.00'))

    # Integración MercadoPago
    mp_preference_id = models.CharField('ID de preferencia MP', max_length=100, blank=True)
    mp_payment_id = models.CharField('ID de pago MP', max_length=100, blank=True)
    mp_status_detail = models.CharField('Detalle de estado MP', max_length=100, blank=True)

    created_at = models.DateTimeField('Creado', auto_now_add=True)
    updated_at = models.DateTimeField('Actualizado', auto_now=True)

    class Meta:
        verbose_name = 'Pedido'
        verbose_name_plural = 'Pedidos'
        ordering = ['-created_at']

    def __str__(self):
        return f'Pedido #{self.id} - {self.customer_name}'

    def recalculate_total(self):
        total = sum((item.subtotal for item in self.items.all()), Decimal('0.00'))
        self.total = total
        self.save(update_fields=['total'])


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    product_name = models.CharField('Nombre del producto', max_length=200)
    unit_price = models.DecimalField('Precio unitario', max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField('Cantidad', default=1)

    class Meta:
        verbose_name = 'Ítem de pedido'
        verbose_name_plural = 'Ítems de pedido'

    def __str__(self):
        return f'{self.quantity} x {self.product_name}'

    @property
    def subtotal(self):
        return self.unit_price * self.quantity
