# Sports Deal — E-commerce de artículos de deporte

Proyecto completo de e-commerce hecho en **Django**, con:

- **Front Office**: catálogo de productos, búsqueda, carrito de compras y checkout.
- **Back Office**: panel de administración (Django Admin) para gestionar productos, stock, categorías y pedidos.
- **Pagos**: integración real con **MercadoPago (Checkout Pro)**, incluyendo webhook para confirmar pagos automáticamente.

---

## 1. Requisitos previos

- Python 3.11 o superior
- Una cuenta de MercadoPago Developers: https://www.mercadopago.com.ar/developers/panel/app

---

## 2. Instalación local (para probar en tu computadora)

```bash
# 1. Descomprimir el proyecto y entrar a la carpeta
cd sportstore

# 2. Crear entorno virtual
python3 -m venv venv
source venv/bin/activate        # En Windows: venv\Scripts\activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar variables de entorno
cp .env.example .env
# Editar el archivo .env y completar MERCADOPAGO_ACCESS_TOKEN (ver paso 4 abajo)

# 5. Crear la base de datos
python manage.py migrate

# 6. Crear tu usuario administrador (Back Office)
python manage.py createsuperuser

# 7. (Opcional) Importar tus productos desde un CSV
python manage.py import_products productos_ejemplo.csv

# 8. Levantar el servidor
python manage.py runserver
```

- Tienda (Front Office): http://127.0.0.1:8000/
- Panel de administración (Back Office): http://127.0.0.1:8000/admin/

---

## 3. Cargar tus productos

Tenés dos opciones:

**a) Uno por uno desde el Back Office** (`/admin/` → Productos → Agregar producto): nombre, descripción, precio, stock, categoría e imagen.

**b) Importación masiva por CSV** con el comando `import_products`. El archivo debe tener estas columnas:

```csv
name,description,price,stock,category
Pelota de fútbol N°5,Pelota oficial tamaño 5,15000,30,Fútbol
Zapatillas running Pro,Zapatillas livianas,45000,15,Calzado
```

```bash
python manage.py import_products tu_archivo.csv
```

> El CSV no sube imágenes — subilas después desde el Back Office, producto por producto.

---

## 4. Configurar MercadoPago (pagos reales)

1. Entrá a https://www.mercadopago.com.ar/developers/panel/app y creá una aplicación.
2. En la sección **Credenciales**, vas a tener dos pares (Public Key + Access Token):
   - **De prueba (TEST-...)**: para testear todo el flujo sin cobrar dinero real. Usá las [tarjetas de prueba de MercadoPago](https://www.mercadopago.com.ar/developers/es/docs/checkout-pro/additional-content/your-integrations/test/cards).
   - **De producción (APP_USR-...)**: para cobrar de verdad, una vez que todo esté probado.
3. Copiá el **Access Token** correspondiente al archivo `.env`:
   ```
   MERCADOPAGO_ACCESS_TOKEN=TEST-xxxxxxxx...
   ```
4. **Importante — Webhook**: MercadoPago necesita poder llegar a `SITE_URL + /pago/webhook/mercadopago/` desde internet para confirmar los pagos. Esto **no funciona en `127.0.0.1`** porque MercadoPago no puede alcanzar tu computadora. Para probar el webhook en desarrollo, usá un túnel como [ngrok](https://ngrok.com/) y poné esa URL pública en `SITE_URL` dentro del `.env`. En producción, usá el dominio real de tu sitio.

---

## 5. Llevarlo a producción

Este proyecto está listo para desplegarse en cualquier hosting que soporte Django/Python (Railway, Render, PythonAnywhere, DigitalOcean, un VPS propio, etc.). Pasos generales:

1. **Base de datos**: cambiar de SQLite a PostgreSQL. En `.env`:
   ```
   DB_ENGINE=postgres
   DB_NAME=...
   DB_USER=...
   DB_PASSWORD=...
   DB_HOST=...
   DB_PORT=5432
   ```
2. **Variables de entorno de producción**:
   ```
   DEBUG=False
   ALLOWED_HOSTS=www.tudominio.com
   SITE_URL=https://www.tudominio.com
   SECRET_KEY=una-clave-larga-y-aleatoria-distinta-a-la-de-desarrollo
   MERCADOPAGO_ACCESS_TOKEN=APP_USR-xxxxxxxx...   (token de producción)
   ```
3. **Archivos estáticos**: `python manage.py collectstatic`
4. **Servidor de producción** (no usar `runserver`):
   ```bash
   gunicorn config.wsgi:application --bind 0.0.0.0:8000
   ```
5. Configurar HTTPS (obligatorio para MercadoPago en producción) y un dominio propio.
6. Hacer un backup regular de la base de datos.

Si querés, en el próximo paso te puedo ayudar puntualmente con la configuración para la plataforma de hosting que elijas.

---

## 6. Estructura del proyecto

```
sportstore/
├── config/            # Configuración del proyecto Django
├── store/             # App principal (modelos, vistas, admin, carrito, pagos)
│   ├── models.py       # Category, Product, Order, OrderItem
│   ├── admin.py         # Back Office (panel de administración)
│   ├── views.py         # Front Office (catálogo, carrito, checkout)
│   ├── cart.py           # Carrito de compras (basado en sesión)
│   ├── payments.py        # Integración con MercadoPago
│   └── management/commands/import_products.py   # Importador CSV
├── templates/store/    # Plantillas HTML del Front Office
├── static/store/        # CSS del sitio
├── requirements.txt
└── .env.example
```

## 7. Usuarios y contraseñas de prueba

Este paquete se entrega **sin** base de datos ni usuario administrador creados — los generás vos en el paso 2.6 (`createsuperuser`) con tus propias credenciales.

---

¿Dudas o querés que te ayude con el próximo paso (deploy, diseño, más funcionalidades como cupones de descuento, envío por correo, etc.)? Solo pedilo.
