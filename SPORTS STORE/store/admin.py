from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Product, Order, OrderItem

admin.site.site_header = 'Sports Deal — Panel de Administración'
admin.site.site_title = 'Sports Deal Back Office'
admin.site.index_title = 'Gestión de la tienda'


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'product_count')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)

    def product_count(self, obj):
        return obj.products.count()
    product_count.short_description = 'Cantidad de productos'


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('thumbnail', 'name', 'category', 'price', 'stock', 'is_active', 'updated_at')
    list_display_links = ('name',)
    list_editable = ('price', 'stock', 'is_active')
    list_filter = ('category', 'is_active')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    list_per_page = 25

    fieldsets = (
        ('Información básica', {
            'fields': ('name', 'slug', 'category', 'description')
        }),
        ('Precio y stock', {
            'fields': ('price', 'stock', 'is_active')
        }),
        ('Imagen', {
            'fields': ('image',)
        }),
    )

    def thumbnail(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="height:40px;border-radius:4px;" />', obj.image.url)
        return '—'
    thumbnail.short_description = 'Imagen'


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'product_name', 'unit_price', 'quantity', 'subtotal')
    can_delete = False

    def subtotal(self, obj):
        return f'${obj.subtotal:,.2f}'
    subtotal.short_description = 'Subtotal'


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer_name', 'email', 'total', 'status_badge', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('customer_name', 'email', 'mp_payment_id', 'mp_preference_id')
    readonly_fields = ('mp_preference_id', 'mp_payment_id', 'mp_status_detail',
                        'total', 'created_at', 'updated_at')
    inlines = (OrderItemInline,)
    list_per_page = 25

    fieldsets = (
        ('Cliente', {
            'fields': ('customer_name', 'email', 'phone', 'address', 'city', 'postal_code', 'notes')
        }),
        ('Estado del pedido', {
            'fields': ('status', 'total')
        }),
        ('Datos de MercadoPago', {
            'fields': ('mp_preference_id', 'mp_payment_id', 'mp_status_detail')
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    def status_badge(self, obj):
        colors = {
            'pending': '#f0ad4e',
            'paid': '#5cb85c',
            'shipped': '#5bc0de',
            'cancelled': '#d9534f',
            'rejected': '#d9534f',
        }
        color = colors.get(obj.status, '#777')
        return format_html(
            '<span style="background:{};color:white;padding:2px 8px;border-radius:10px;font-size:11px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Estado'

    actions = ['mark_as_shipped', 'mark_as_cancelled']

    def mark_as_shipped(self, request, queryset):
        updated = queryset.update(status='shipped')
        self.message_user(request, f'{updated} pedido(s) marcados como enviados.')
    mark_as_shipped.short_description = 'Marcar como enviado'

    def mark_as_cancelled(self, request, queryset):
        updated = queryset.update(status='cancelled')
        self.message_user(request, f'{updated} pedido(s) cancelados.')
    mark_as_cancelled.short_description = 'Cancelar pedido(s)'
