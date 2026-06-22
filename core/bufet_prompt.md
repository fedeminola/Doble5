**ROL:** SSE DJango

**Objetivo:** Integrar un nuevo módulo para la gestión de ventas de artículos (buffet/tienda) en el sistema "Cancha-Admin". Esto incluye gestión de inventario, compras a proveedores y una caja separada para estas operaciones.

**Stack Tecnológico:** Continuar con el stack existente (Django, PostgreSQL, Django Unfold, Docker).

---

### **1. Modificaciones a la Arquitectura Existente**

#### **1.1. Modelos (`core/models.py`)**

Se debe modificar el modelo `Caja` para que pueda gestionar múltiples tipos de caja en un mismo día y sede.

*   **Modelo `Caja`:**
    *   Añadir un campo `tipo` con opciones predefinidas (`'CANCHA'`, `'BUFET'`).
    *   Cambiar la restricción `unique=True` en el campo `fecha` por una restricción `unique_together` que abarque `('fecha', 'sede', 'tipo')`. Esto permitirá tener una caja de cancha y una de buffet abiertas simultáneamente para la misma fecha y sede.

*   **Modelo `MovimientoCaja`:**
    *   Añadir una relación `ForeignKey` opcional a los nuevos modelos `Venta` y `Compra` para mejorar la trazabilidad de los movimientos.

#### **1.2. Panel de Administración (`core/admin.py`)**

*   **`CajaAdmin`:**
    *   Añadir el nuevo campo `tipo` a `list_display` y `list_filter` para poder diferenciar las cajas de un vistazo.
*   **`MovimientoCajaAdmin`:**
    *   Mejorar el filtro para que se pueda buscar por el tipo de caja (`caja__tipo`).

---

### **2. Nuevos Modelos de Datos (`core/models.py`)**

Implementa los siguientes modelos para gestionar los artículos, el stock, las ventas y las compras.

```python
# core/models.py (Nuevos modelos)

class Articulo(models.Model):
    descripcion = models.CharField(max_length=255, unique=True)
    precio_costo = models.DecimalField(max_digits=10, decimal_places=2)
    precio_venta = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField(default=0, help_text="Stock actual. Se actualiza automáticamente con ventas y compras.")
    stock_minimo = models.PositiveIntegerField(default=0)
    sede = models.ForeignKey(Sede, on_delete=models.CASCADE) # Asociar artículo a una sede

    def __str__(self):
        return self.descripcion

class Proveedor(models.Model):
    nombre = models.CharField(max_length=200, unique=True)
    # ... otros campos como CUIT, teléfono, etc.

    def __str__(self):
        return self.nombre

class Venta(models.Model):
    caja = models.ForeignKey(Caja, on_delete=models.PROTECT, limit_choices_to={'tipo': 'BUFET', 'abierta': True})
    fecha = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(User, on_delete=models.PROTECT)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    articulos = models.ManyToManyField(Articulo, through='ItemVenta')

class ItemVenta(models.Model):
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE)
    articulo = models.ForeignKey(Articulo, on_delete=models.PROTECT)
    cantidad = models.PositiveIntegerField(default=1)
    precio_venta_momento = models.DecimalField(max_digits=10, decimal_places=2, help_text="Precio al momento de la venta")

class Compra(models.Model):
    proveedor = models.ForeignKey(Proveedor, on_delete=models.PROTECT)
    fecha = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(User, on_delete=models.PROTECT)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    articulos = models.ManyToManyField(Articulo, through='ItemCompra')

class ItemCompra(models.Model):
    compra = models.ForeignKey(Compra, on_delete=models.CASCADE)
    articulo = models.ForeignKey(Articulo, on_delete=models.PROTECT)
    cantidad = models.PositiveIntegerField(default=1)
    precio_costo_momento = models.DecimalField(max_digits=10, decimal_places=2, help_text="Costo al momento de la compra")
```

---

### **3. Lógica de Negocio y Funcionalidades**

#### **3.1. Gestión de Stock**
*   **Al guardar una `Venta`:** Itera sobre sus `ItemVenta`. Por cada item, **resta** la `cantidad` del `stock` del `Articulo` correspondiente. El sistema **debe permitir** que el stock resulte en un número negativo.
*   **Al guardar una `Compra`:** Itera sobre sus `ItemCompra`. Por cada item, **suma** la `cantidad` al `stock` del `Articulo` correspondiente.

#### **3.2. Flujo de Venta**
**Nota para el desarrollador:** Asegúrate de envolver las operaciones de escritura complejas (ej. guardar Venta + Items + Movimientos de Caja) en una transacción de base de datos (`@transaction.atomic`) para garantizar la integridad de los datos.
1.  **Crear una vista personalizada de Django para la "Pantalla de Venta"**. Esta vista debe:
    *   Requerir que exista una "Caja Bufet" abierta para poder operar.
    *   Usar un formulario para `Venta` y un `formset` para `ItemVenta`.
    *   Permitir añadir artículos dinámicamente (usando JavaScript/HTMX). Al seleccionar un artículo, su `precio_venta` debe cargarse automáticamente en el formulario del item.
    *   Calcular el `total` de la venta en tiempo real en la interfaz.
    *   Incluir campos para `monto_pagado_efectivo` y `monto_pagado_transferencia`. La interfaz debe calcular y mostrar el "vuelto" o "restante" (`(efectivo + transferencia) - total`), pero este valor no se guarda.
2.  **Al guardar la `Venta`:**
    *   Validar que la suma de los pagos sea igual o mayor al total.
    *   Crear automáticamente los `MovimientoCaja` correspondientes en la "Caja Bufet" activa:
        *   Un movimiento de `ingreso` por el `monto_pagado_efectivo`.
        *   Un movimiento de `ingreso` (método 'banco') por el `monto_pagado_transferencia`.
        *   Asociar estos movimientos a la venta recién creada.

#### **3.3. Flujo de Compra**
1.  Implementar un CRUD en el admin para `Proveedor` y `Compra`.
2.  El formulario de `Compra` debe usar un `inline` para `ItemCompra`.
3.  **Importante:** Guardar una `Compra` **NO** debe generar un egreso automático. El pago de la compra se debe registrar manualmente desde la vista de "Caja Bufet", creando un `MovimientoCaja` de tipo `egreso` y asociándolo (opcionalmente) a la `Compra` correspondiente.

#### **3.4. Reportes y Alertas**
*   Crear una nueva vista en el admin (o una vista personalizada) llamada "Artículos con Stock Bajo", que liste todos los `Articulo` donde `stock <= stock_minimo`.

---

### **4. Permisos y Roles**

*   **Rol `Empleado`:**
    *   **PUEDE:** Realizar ventas, registrar compras a proveedores, abrir y cerrar cajas (tanto de cancha como de buffet).
    *   **NO PUEDE:** Modificar los datos maestros de un `Articulo` (`descripcion`, `precio_costo`, `precio_venta`, `stock_minimo`). Tampoco puede ajustar el `stock` manualmente.
    *   **NO PUEDE:** Ver reportes financieros consolidados.

---

### **5. Cambios Sugeridos en Ficheros**

A continuación se presentan los diffs sugeridos para los ficheros existentes.

```diff
--- a/core/admin.py
+++ b/core/admin.py
@@ -6,8 +6,10 @@
 from .models import (
     Sede, Cancha, Cliente, Turno, Caja, MovimientoCaja,
-    ClientePublicidad, ContratoPublicidad, Notificacion, Configuracion
+    ClientePublicidad, ContratoPublicidad, Notificacion, Configuracion,
+    Articulo, Proveedor, Venta, ItemVenta, Compra, ItemCompra
 )
 
 @admin.register(Configuracion)
@@ -37,16 +39,47 @@
 class MovimientoCajaAdmin(ModelAdmin):
     list_display = ('caja', 'tipo', 'metodo_pago', 'monto', 'usuario', 'descripcion')
-    list_filter = ('caja__sede', 'tipo', 'metodo_pago', 'usuario')
+    list_filter = ('caja__sede', 'caja__tipo', 'tipo', 'metodo_pago', 'usuario')
 
 class CajaAdmin(ModelAdmin):
-    list_display = ('sede', 'fecha', 'usuario_apertura', 'abierta', 'monto_inicial', 'monto_final_real', 'diferencia')
-    list_filter = ('sede', 'abierta', 'fecha')
+    list_display = ('sede', 'fecha', 'tipo', 'usuario_apertura', 'abierta', 'monto_inicial', 'monto_final_real', 'diferencia')
+    list_filter = ('sede', 'tipo', 'abierta', 'fecha')
     readonly_fields = ('monto_final_teorico', 'diferencia')
+
+class ItemVentaInline(admin.TabularInline):
+    model = ItemVenta
+    extra = 1
+
+@admin.register(Venta)
+class VentaAdmin(ModelAdmin):
+    inlines = [ItemVentaInline]
+    list_display = ('fecha', 'caja', 'usuario', 'total')
+    readonly_fields = ('total',)
+
+class ItemCompraInline(admin.TabularInline):
+    model = ItemCompra
+    extra = 1
+
+@admin.register(Compra)
+class CompraAdmin(ModelAdmin):
+    inlines = [ItemCompraInline]
+    list_display = ('fecha', 'proveedor', 'usuario', 'total')
+    readonly_fields = ('total',)
+
+@admin.register(Articulo)
+class ArticuloAdmin(ModelAdmin):
+    list_display = ('descripcion', 'sede', 'precio_costo', 'precio_venta', 'stock', 'stock_minimo')
+    list_filter = ('sede',)
+    search_fields = ('descripcion',)
+    readonly_fields = ('stock',)
 
 admin.site.register(Sede, ModelAdmin)
 admin.site.register(Cancha, ModelAdmin)
@@ -58,3 +90,4 @@
 admin.site.register(ClientePublicidad, ModelAdmin)
 admin.site.register(ContratoPublicidad, ModelAdmin)
 admin.site.register(Notificacion, ModelAdmin)
+admin.site.register(Proveedor, ModelAdmin)

```