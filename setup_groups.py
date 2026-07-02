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
    # --- Grupo Administrador ---
    admin_group, _ = Group.objects.get_or_create(name='Administrador')
    # Los administradores tienen todos los permisos por defecto, no es necesario asignarlos explícitamente
    # si su usuario es `is_superuser`. Si no, se les deben asignar todos los permisos aquí.

    # --- Grupo Empleado ---
    empleado_group, _ = Group.objects.get_or_create(name='Empleado')

    # Permisos para Empleado
    empleado_models = [
        Turno, MovimientoCaja, Cliente, Caja, Articulo, Venta, Compra, Proveedor
    ]
    empleado_codenames = [
        'add_turno', 'change_turno', 'delete_turno', 'view_turno',
        'add_movimientocaja', 'change_movimientocaja', 'view_movimientocaja',
        'add_cliente', 'change_cliente', 'view_cliente',
        'add_caja', 'change_caja', 'view_caja',
        'view_articulo', 'add_articulo', 'change_articulo',
        'add_venta', 'view_venta',
        'add_compra', 'view_compra',
        'add_proveedor', 'view_proveedor', 'change_proveedor',
    ]
    
    empleado_permissions = []
    for model in empleado_models:
        ct = ContentType.objects.get_for_model(model)
        for perm in Permission.objects.filter(content_type=ct):
            if perm.codename in empleado_codenames:
                empleado_permissions.append(perm)

    empleado_group.permissions.set(empleado_permissions)

    # --- Grupo Visualizador ---
    visualizador_group, _ = Group.objects.get_or_create(name='Visualizador')
    
    visualizador_models = [
        Sede, Cancha, Caja, Articulo, Proveedor, Cliente, MovimientoCaja
    ]
    
    visualizador_permissions = []
    for model in visualizador_models:
        ct = ContentType.objects.get_for_model(model)
        # Asignar solo el permiso de 'view'
        view_perm = Permission.objects.filter(content_type=ct, codename__startswith='view_').first()
        if view_perm:
            visualizador_permissions.append(view_perm)
            
    visualizador_group.permissions.set(visualizador_permissions)

    print("Grupos y permisos 'Empleado' y 'Visualizador' configurados correctamente.")

if __name__ == "__main__":
    setup_groups()