
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Doble5.settings')
django.setup()

from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from core.models import (
    Turno, MovimientoCaja, Cliente, Sede, Cancha, Caja,
    Articulo, Venta, Compra, Proveedor
)

def setup_groups():
    admin_group, _ = Group.objects.get_or_create(name='Administrador')
    empleado_group, _ = Group.objects.get_or_create(name='Empleado')

    # Permisos para Empleado
    turno_ct = ContentType.objects.get_for_model(Turno)
    movimiento_ct = ContentType.objects.get_for_model(MovimientoCaja)
    cliente_ct = ContentType.objects.get_for_model(Cliente)
    caja_ct = ContentType.objects.get_for_model(Caja)
    articulo_ct = ContentType.objects.get_for_model(Articulo)
    venta_ct = ContentType.objects.get_for_model(Venta)
    compra_ct = ContentType.objects.get_for_model(Compra)
    proveedor_ct = ContentType.objects.get_for_model(Proveedor)
    
    turno_perms = Permission.objects.filter(content_type=turno_ct, codename__in=['add_turno', 'change_turno', 'delete_turno', 'view_turno'])
    movimiento_perms = Permission.objects.filter(content_type=movimiento_ct, codename__in=['add_movimientocaja', 'change_movimientocaja', 'view_movimientocaja'])
    cliente_perms = Permission.objects.filter(content_type=cliente_ct, codename__in=['add_cliente', 'change_cliente', 'view_cliente'])
    caja_perms = Permission.objects.filter(content_type=caja_ct, codename__in=['add_caja', 'change_caja', 'view_caja'])
    articulo_perms = Permission.objects.filter(content_type=articulo_ct, codename__in=['view_articulo'])
    venta_perms = Permission.objects.filter(content_type=venta_ct, codename__in=['add_venta', 'view_venta'])
    compra_perms = Permission.objects.filter(content_type=compra_ct, codename__in=['add_compra', 'view_compra'])
    proveedor_perms = Permission.objects.filter(content_type=proveedor_ct, codename__in=['add_proveedor', 'view_proveedor', 'change_proveedor'])
    
    all_perms = (
        list(turno_perms) + list(movimiento_perms) + list(cliente_perms) + 
        list(caja_perms) + list(articulo_perms) + list(venta_perms) + 
        list(compra_perms) + list(proveedor_perms)
    )
    
    empleado_group.permissions.set(all_perms)
    
    print("Grupos y permisos configurados correctamente.")

if __name__ == "__main__":
    setup_groups()
