from django.urls import path
from . import views

urlpatterns = [
    path('caja/abrir/', views.abrir_caja, name='abrir_caja'),
    path('caja/cerrar/', views.cerrar_caja, name='cerrar_caja'),
    path('reportes/diario/', views.reporte_diario, name='reporte_diario'),
    path('reportes/mensual/', views.reporte_mensual, name='reporte_mensual'),
    path('reportes/semanal/', views.reporte_semanal, name='reporte_semanal'),
    path('export/reporte_diario_csv/', views.export_reporte_diario_csv, name='export_reporte_diario_csv'),
    path('export/reporte_mensual_csv/', views.export_reporte_mensual_csv, name='export_reporte_mensual_csv'),

    # Turnos
    path('turno-grid/', views.turno_grid, name='turno_grid'),
    path('turno-delete/<int:turno_id>/', views.eliminar_turno, name='eliminar_turno'),

    # Ventas y Compras
    path('ventas/registrar/', views.registrar_venta, name='registrar_venta'),
    path('compras/registrar/', views.registrar_compra, name='registrar_compra'),
    
    # API para autocomplete
    path('api/buscar-articulos/', views.buscar_articulos, name='buscar_articulos'),
]