from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from unfold.admin import ModelAdmin
from .models import (
    Sede, Cancha, Cliente, Turno, Caja, MovimientoCaja,
    ClientePublicidad, ContratoPublicidad, Notificacion, Configuracion,
    Articulo, Proveedor, Venta, ItemVenta, Compra, ItemCompra, UserProfile
)

# Inline admin for UserProfile
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Sede'

# Define a new User admin
class UserAdmin(BaseUserAdmin, ModelAdmin):
    inlines = (UserProfileInline,)

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

@admin.register(Configuracion)
class ConfiguracionAdmin(ModelAdmin):
    def has_add_permission(self, request):
        return not self.model.objects.exists()
    def has_delete_permission(self, request, obj=None):
        return False

class TurnoAdmin(ModelAdmin):
    list_display = ('cancha', 'fecha_hora_inicio', 'estado', 'cliente', 'precio_total')
    list_filter = ('estado', 'cancha__sede', 'cancha')
    search_fields = ('cliente__nombre', 'cliente__telefono')

    def save_model(self, request, obj, form, change):
        obj.save(user=request.user)

class MovimientoCajaAdmin(ModelAdmin):
    list_display = ('caja', 'tipo', 'metodo_pago', 'monto', 'usuario', 'descripcion')
    list_filter = ('caja__sede', 'caja__tipo', 'tipo', 'metodo_pago', 'usuario')

# Inline para mostrar los movimientos dentro de la vista de Caja
class MovimientoCajaInline(admin.TabularInline):
    model = MovimientoCaja
    extra = 0  # No mostrar formularios extra para añadir
    fields = ( 'usuario', 'tipo', 'metodo_pago', 'monto', 'descripcion')
    readonly_fields = fields  # Hacer todos los campos de solo lectura
    can_delete = False  # No permitir borrar desde aquí

    def has_add_permission(self, request, obj=None):
        # No permitir añadir nuevos movimientos desde el inline
        return False

class CajaAdmin(ModelAdmin):
    list_display = ('sede', 'fecha', 'tipo', 'usuario_apertura', 'abierta', 'monto_inicial', 'monto_final_real', 'diferencia')
    list_filter = ('sede', 'tipo', 'abierta', 'fecha')
    readonly_fields = ('monto_final_teorico', 'diferencia')
    # Aquí agregamos la "pestaña" de movimientos
    inlines = [MovimientoCajaInline]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('sede', 'usuario_apertura', 'usuario_cierre')


class ItemVentaInline(admin.TabularInline):
    model = ItemVenta
    extra = 1
    readonly_fields = ('precio_venta_momento',)

@admin.register(Venta)
class VentaAdmin(ModelAdmin):
    inlines = [ItemVentaInline]
    list_display = ('fecha', 'caja', 'usuario', 'total')
    readonly_fields = ('total',)

class ItemCompraInline(admin.TabularInline):
    model = ItemCompra
    extra = 1

@admin.register(Compra)
class CompraAdmin(ModelAdmin):
    inlines = [ItemCompraInline]
    list_display = ('fecha', 'proveedor', 'usuario', 'total')
    readonly_fields = ('total',)

@admin.register(Articulo)
class ArticuloAdmin(ModelAdmin):
    list_display = ('descripcion', 'sede', 'precio_costo', 'precio_venta', 'stock', 'stock_minimo')
    list_filter = ('sede',)
    search_fields = ('descripcion',)
    readonly_fields = ('stock',)

admin.site.register(Sede, ModelAdmin)
admin.site.register(Cancha, ModelAdmin)
admin.site.register(Cliente, ModelAdmin)
admin.site.register(Turno, TurnoAdmin)
admin.site.register(MovimientoCaja, MovimientoCajaAdmin)
admin.site.register(Caja, CajaAdmin)
admin.site.register(ClientePublicidad, ModelAdmin)
admin.site.register(ContratoPublicidad, ModelAdmin)
admin.site.register(Notificacion, ModelAdmin)
admin.site.register(Proveedor, ModelAdmin)
