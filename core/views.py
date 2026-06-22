import csv
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.contrib import messages
from django.db import transaction
from django.db.models import Sum, Q
from .models import (
    Caja, MovimientoCaja, Notificacion, Sede, Cancha, Turno, Cliente, 
    Configuracion, Articulo, Venta, ItemVenta, Compra, ItemCompra, Proveedor, UserProfile
)
from .forms import VentaForm, ItemVentaFormSet, CompraForm, ItemCompraFormSet
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User
from decimal import Decimal
from datetime import datetime, time, timedelta
from collections import defaultdict
from .decorators import group_required


# --- Vistas de Reportes y Exportación ---

@login_required
@group_required('Administrador')
def export_reporte_diario_csv(request):
    import tablib
    selected_date_str = request.GET.get('date', timezone.now().strftime('%Y-%m-%d'))
    tipo_caja = request.GET.get('tipo_caja', 'CANCHA')
    try:
        selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
    except ValueError:
        selected_date = timezone.now().date()
        selected_date_str = selected_date.strftime('%Y-%m-%d')

    headers = ('Fecha', 'Sede', 'Tipo Caja', 'Monto Inicial', 'Ingresos Efectivo', 'Ingresos Banco', 'Total Ingresos',
               'Total Egresos', 'Balance Final')
    data = tablib.Dataset(headers=headers)

    cajas = Caja.objects.filter(fecha=selected_date, tipo=tipo_caja)

    for caja in cajas:
        ingresos_efectivo = \
        MovimientoCaja.objects.filter(caja=caja, tipo='ingreso', metodo_pago='efectivo').aggregate(total=Sum('monto'))[
            'total'] or Decimal('0.00')
        ingresos_banco = \
        MovimientoCaja.objects.filter(caja=caja, tipo='ingreso', metodo_pago='banco').aggregate(total=Sum('monto'))[
            'total'] or Decimal('0.00')
        total_ingresos = ingresos_efectivo + ingresos_banco
        total_egresos = MovimientoCaja.objects.filter(caja=caja, tipo='egreso').aggregate(total=Sum('monto'))[
                            'total'] or Decimal('0.00')
        balance_final = caja.monto_inicial + ingresos_efectivo - total_egresos if caja.abierta else caja.monto_final_real

        data.append(
            (caja.fecha, caja.sede.nombre, caja.get_tipo_display(), caja.monto_inicial, ingresos_efectivo, ingresos_banco, total_ingresos,
             total_egresos, balance_final))

    export_format = request.GET.get('format', 'csv')
    if export_format == 'xls':
        response = HttpResponse(data.export('xls'), content_type='application/vnd.ms-excel')
        response['Content-Disposition'] = f'attachment; filename="reporte_diario_{selected_date_str}_{tipo_caja}.xls"'
    else:
        response = HttpResponse(data.export('csv'), content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="reporte_diario_{selected_date_str}_{tipo_caja}.csv"'

    return response


@login_required
@group_required('Administrador')
def export_reporte_mensual_csv(request):
    import tablib
    today = timezone.now()
    selected_month = int(request.GET.get('month', today.month))
    selected_year = int(request.GET.get('year', today.year))
    tipo_caja = request.GET.get('tipo_caja', 'CANCHA')

    headers = ('Mes', 'Año', 'Tipo Caja', 'Total Ingresos', 'Total Egresos', 'Ganancia/Pérdida')
    data = tablib.Dataset(headers=headers)

    total_ingresos = MovimientoCaja.objects.filter(caja__fecha__month=selected_month, caja__fecha__year=selected_year,
                                                   caja__tipo=tipo_caja, tipo='ingreso').aggregate(total=Sum('monto'))['total'] or Decimal(
        '0.00')
    total_egresos = MovimientoCaja.objects.filter(caja__fecha__month=selected_month, caja__fecha__year=selected_year,
                                                  caja__tipo=tipo_caja, tipo='egreso').aggregate(total=Sum('monto'))['total'] or Decimal(
        '0.00')
    ganancia = total_ingresos - total_egresos

    data.append((selected_month, selected_year, tipo_caja, total_ingresos, total_egresos, ganancia))

    export_format = request.GET.get('format', 'csv')
    if export_format == 'xls':
        response = HttpResponse(data.export('xls'), content_type='application/vnd.ms-excel')
        response['Content-Disposition'] = f'attachment; filename="reporte_mensual_{selected_year}_{selected_month}_{tipo_caja}.xls"'
    else:
        response = HttpResponse(data.export('csv'), content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="reporte_mensual_{selected_year}_{selected_month}_{tipo_caja}.csv"'

    return response


@login_required
@group_required('Administrador')
def reporte_mensual(request):
    today = timezone.now()
    selected_month = int(request.GET.get('month', today.month))
    selected_year = int(request.GET.get('year', today.year))
    tipo_caja = request.GET.get('tipo_caja', 'CANCHA')

    total_ingresos = MovimientoCaja.objects.filter(caja__fecha__month=selected_month, caja__fecha__year=selected_year,
                                                   caja__tipo=tipo_caja, tipo='ingreso').aggregate(total=Sum('monto'))['total'] or Decimal(
        '0.00')
    total_egresos = MovimientoCaja.objects.filter(caja__fecha__month=selected_month, caja__fecha__year=selected_year,
                                                  caja__tipo=tipo_caja, tipo='egreso').aggregate(total=Sum('monto'))['total'] or Decimal(
        '0.00')
    ganancia = total_ingresos - total_egresos

    cantidad_turnos = Turno.objects.filter(
        fecha_hora_inicio__month=selected_month,
        fecha_hora_inicio__year=selected_year,
        estado='ocupado'
    ).count()

    context = {
        'selected_month': selected_month,
        'selected_year': selected_year,
        'total_ingresos': total_ingresos,
        'total_egresos': total_egresos,
        'ganancia': ganancia,
        'cantidad_turnos': cantidad_turnos,
        'months': range(1, 13),
        'years': range(2023, today.year + 1),
        'tipo_caja': tipo_caja,
        'tipos_caja': Caja.TIPOS,
    }
    return render(request, 'core/reporte_mensual.html', context)


@login_required
@group_required('Administrador')
def reporte_diario(request):
    selected_date_str = request.GET.get('date', timezone.now().strftime('%Y-%m-%d'))
    tipo_caja = request.GET.get('tipo_caja', 'CANCHA')
    try:
        selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
    except ValueError:
        selected_date = timezone.now().date()
        selected_date_str = selected_date.strftime('%Y-%m-%d')

    caja = Caja.objects.filter(fecha=selected_date, tipo=tipo_caja).first()

    report_data = None
    if caja:
        ingresos_efectivo = \
        MovimientoCaja.objects.filter(caja=caja, tipo='ingreso', metodo_pago='efectivo').aggregate(total=Sum('monto'))[
            'total'] or Decimal('0.00')
        ingresos_banco = \
        MovimientoCaja.objects.filter(caja=caja, tipo='ingreso', metodo_pago='banco').aggregate(total=Sum('monto'))[
            'total'] or Decimal('0.00')
        total_ingresos = ingresos_efectivo + ingresos_banco
        total_egresos = MovimientoCaja.objects.filter(caja=caja, tipo='egreso').aggregate(total=Sum('monto'))[
                            'total'] or Decimal('0.00')
        
        specific_data = {}
        if tipo_caja == 'CANCHA':
            specific_data['turnos_count'] = Turno.objects.filter(cancha__sede=caja.sede, fecha_hora_inicio__date=selected_date, estado='ocupado').count()
        elif tipo_caja == 'BUFET':
            specific_data['ventas_count'] = Venta.objects.filter(caja=caja).count()


        report_data = {
            'caja': caja,
            'ingresos_efectivo': ingresos_efectivo,
            'ingresos_banco': ingresos_banco,
            'total_ingresos': total_ingresos,
            'total_egresos': total_egresos,
            'balance_final': caja.monto_inicial + ingresos_efectivo - total_egresos if caja.abierta else caja.monto_final_real,
            'specific_data': specific_data,
        }

    context = {
        'selected_date_str': selected_date_str,
        'report_data': report_data,
        'tipo_caja': tipo_caja,
        'tipos_caja': Caja.TIPOS,
    }
    return render(request, 'core/reporte_diario.html', context)


@login_required
@group_required('Administrador')
def reporte_semanal(request):
    selected_date_str = request.GET.get('date', timezone.now().strftime('%Y-%m-%d'))
    tipo_caja = request.GET.get('tipo_caja', 'CANCHA')
    try:
        selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
    except ValueError:
        selected_date = timezone.now().date()

    start_week = selected_date - timedelta(days=selected_date.weekday())
    end_week = start_week + timedelta(days=6)

    total_ingresos = MovimientoCaja.objects.filter(
        caja__fecha__range=[start_week, end_week],
        caja__tipo=tipo_caja,
        tipo='ingreso'
    ).aggregate(total=Sum('monto'))['total'] or Decimal('0.00')

    total_egresos = MovimientoCaja.objects.filter(
        caja__fecha__range=[start_week, end_week],
        caja__tipo=tipo_caja,
        tipo='egreso'
    ).aggregate(total=Sum('monto'))['total'] or Decimal('0.00')

    ganancia = total_ingresos - total_egresos

    context = {
        'selected_date_str': selected_date.strftime('%Y-%m-%d'),
        'start_week': start_week,
        'end_week': end_week,
        'total_ingresos': total_ingresos,
        'total_egresos': total_egresos,
        'ganancia': ganancia,
        'tipo_caja': tipo_caja,
        'tipos_caja': Caja.TIPOS,
    }
    return render(request, 'core/reporte_semanal.html', context)


# --- Vistas de Turnos ---
@login_required
def eliminar_turno(request, turno_id):
    turno = get_object_or_404(Turno, id=turno_id)
    if request.method == 'POST':
        user = request.user
        monto_efectivo = turno.monto_efectivo
        monto_transferencia = turno.monto_transferencia

        if monto_efectivo > 0 or monto_transferencia > 0:
            admins = User.objects.filter(groups__name='Administrador')
            for admin in admins:
                Notificacion.objects.create(
                    usuario=admin,
                    mensaje=f"El usuario {user.username} eliminó un turno que tenía pagos registrados (Efectivo: ${monto_efectivo}, Transf: ${monto_transferencia}). Turno: {turno}"
                )

        LogEntry.objects.log_action(
            user_id=user.id,
            content_type_id=ContentType.objects.get_for_model(Turno).pk,
            object_id=turno.pk,
            object_repr=str(turno),
            action_flag=DELETION,
            change_message=f"Turno eliminado por {user.username}"
        )

        turno.delete()
        messages.success(request, "Turno eliminado exitosamente.")
    return redirect('turno_grid')


@login_required
def turno_grid(request):
    selected_date_str = request.GET.get('date', timezone.now().strftime('%Y-%m-%d'))
    view_mode = request.GET.get('view', 'day')  # 'day' o 'week'
    try:
        selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
    except ValueError:
        selected_date = timezone.now().date()
        selected_date_str = selected_date.strftime('%Y-%m-%d')

    sede_id = request.GET.get('sede')
    sedes = Sede.objects.all()
    if not sede_id and sedes.exists():
        selected_sede = sedes.first()
    else:
        selected_sede = Sede.objects.get(id=sede_id) if sede_id else None

    caja_abierta = False
    if selected_sede:
        caja_abierta = Caja.objects.filter(sede=selected_sede, fecha=selected_date, abierta=True, tipo='CANCHA').exists()

    if request.method == 'POST' and ('nuevo_turno' in request.POST or 'editar_turno' in request.POST):
        turno_id = request.POST.get('turno_id')
        cancha_id = request.POST.get('cancha_id')
        hora = int(request.POST.get('hora'))
        # Usar la fecha enviada por el modal si existe, sino la de la URL
        modal_date_str = request.POST.get('date')
        if modal_date_str:
            try:
                creation_date = datetime.strptime(modal_date_str, '%Y-%m-%d').date()
            except ValueError:
                creation_date = selected_date
        else:
            creation_date = selected_date

        config = Configuracion.objects.first()
        precio_config = config.precio_turno if config else Decimal('0')

        telefono = request.POST.get('telefono')
        nombre_cliente = request.POST.get('nombre_cliente')
        # precio_total ahora viene de la configuracion y no se edita (se toma de config)
        precio_total = precio_config
        monto_efectivo = Decimal(request.POST.get('monto_efectivo', '0'))
        monto_transferencia = Decimal(request.POST.get('monto_transferencia', '0'))

        # Validacion de montos
        if (monto_efectivo + monto_transferencia) != precio_total:
            admins = User.objects.filter(groups__name='Administrador')
            for admin in admins:
                Notificacion.objects.create(
                    usuario=admin,
                    mensaje=f"Discrepancia de monto en turno de {nombre_cliente}. Precio esperado: ${precio_total}, Recibido: ${monto_efectivo + monto_transferencia} (Ef: ${monto_efectivo}, Transf: ${monto_transferencia}). Acción realizada por {request.user.username}."
                )

        if telefono:
            cliente, created = Cliente.objects.get_or_create(
                telefono=telefono,
                defaults={'nombre': nombre_cliente}
            )
        else:
            cliente = Cliente.objects.create(nombre=nombre_cliente or "Sin Nombre")

        cancha = Cancha.objects.get(id=cancha_id)
        # Para edición, necesitamos saber la fecha del turno original si estamos en vista semanal
        if 'editar_turno' in request.POST:
            turno = get_object_or_404(Turno, id=turno_id)
            turno.cliente = cliente
            turno.precio_total = precio_total
            turno.monto_efectivo = monto_efectivo
            turno.monto_transferencia = monto_transferencia
            turno.save(user=request.user)

            LogEntry.objects.log_action(
                user_id=request.user.id,
                content_type_id=ContentType.objects.get_for_model(Turno).pk,
                object_id=turno.pk,
                object_repr=str(turno),
                action_flag=CHANGE,
                change_message=f"Turno editado desde grilla por {request.user.username}"
            )
            messages.success(request, f"Turno de {cliente.nombre} actualizado.")
        else:
            inicio = timezone.make_aware(datetime.combine(creation_date, time(hora)))
            fin = timezone.make_aware(datetime.combine(creation_date, time(hora + 1)))

            turno = Turno.objects.create(
                cancha=cancha,
                cliente=cliente,
                fecha_hora_inicio=inicio,
                fecha_hora_fin=fin,
                estado='ocupado',
                precio_total=precio_total,
                monto_efectivo=monto_efectivo,
                monto_transferencia=monto_transferencia
            )
            turno.save(user=request.user)

            LogEntry.objects.log_action(
                user_id=request.user.id,
                content_type_id=ContentType.objects.get_for_model(Turno).pk,
                object_id=turno.pk,
                object_repr=str(turno),
                action_flag=ADDITION,
                change_message=f"Turno creado desde grilla por {request.user.username}"
            )
            messages.success(request, f"Turno creado con éxito para {cliente.nombre}")

        return redirect(
            f"{request.path}?date={selected_date_str}&sede={selected_sede.id if selected_sede else ''}&view={view_mode}")

    canchas = Cancha.objects.filter(sede=selected_sede) if selected_sede else []
    time_slots = [time(h) for h in range(13, 24)]

    if view_mode == 'week':
        start_week = selected_date - timedelta(days=selected_date.weekday())
        days_range = [start_week + timedelta(days=i) for i in range(7)]

        turnos = Turno.objects.filter(
            cancha__sede=selected_sede,
            fecha_hora_inicio__date__range=[days_range[0], days_range[-1]]
        ).select_related('cancha', 'cliente')

        # Estructura: grid[cancha_id][dia][hora]
        turnos_grid = {c.id: {d: {} for d in days_range} for c in canchas}
        for t in turnos:
            d = t.fecha_hora_inicio.date()
            h = t.fecha_hora_inicio.hour
            if t.cancha.id in turnos_grid and d in turnos_grid[t.cancha.id]:
                turnos_grid[t.cancha.id][d][h] = t

        context = {
            'view_mode': 'week',
            'days_range': days_range,
            'prev_week': (selected_date - timedelta(days=7)).strftime('%Y-%m-%d'),
            'next_week': (selected_date + timedelta(days=7)).strftime('%Y-%m-%d'),
        }
    else:
        turnos = Turno.objects.filter(
            cancha__sede=selected_sede,
            fecha_hora_inicio__date=selected_date
        ).select_related('cancha', 'cliente')

        turnos_grid = {c.id: {h: None for h in range(13, 24)} for c in canchas}
        for t in turnos:
            h = t.fecha_hora_inicio.hour
            if t.cancha.id in turnos_grid and h in turnos_grid[t.cancha.id]:
                turnos_grid[t.cancha.id][h] = t

        context = {
            'view_mode': 'day',
            'selected_date': selected_date,
            'prev_day': (selected_date - timedelta(days=1)).strftime('%Y-%m-%d'),
            'next_day': (selected_date + timedelta(days=1)).strftime('%Y-%m-%d'),
        }

    context.update({
        'sedes': sedes,
        'selected_sede': selected_sede,
        'canchas': canchas,
        'time_slots': time_slots,
        'turnos_grid': turnos_grid,
        'selected_date_str': selected_date_str,
        'precio_sugerido': Configuracion.objects.first().precio_turno if Configuracion.objects.exists() else 0,
        'caja_abierta': caja_abierta,
    })
    return render(request, 'core/turno_grid.html', context)


# --- Vistas de Ventas y Compras ---

@login_required
def registrar_venta(request):
    try:
        sede = request.user.userprofile.sede
        if not sede:
            raise UserProfile.DoesNotExist
    except UserProfile.DoesNotExist:
        messages.error(request, "Tu usuario no está asociado a ninguna sede.")
        return redirect('admin:index')

    caja_abierta = Caja.objects.filter(sede=sede, tipo='BUFET', abierta=True).first()

    if request.method == 'POST':
        if not caja_abierta:
            messages.error(request, "Debe abrir una caja de buffet para realizar ventas.")
            return redirect('registrar_venta')
        
        form = VentaForm(request.POST)
        formset = ItemVentaFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    venta = form.save(commit=False)
                    venta.usuario = request.user
                    venta.caja = caja_abierta
                    venta.save()
                    
                    items = formset.save(commit=False)
                    total_venta = 0
                    for item in items:
                        item.venta = venta
                        # Use the price submitted in the form (which might have been edited)
                        # or fallback to current price if somehow missing
                        if not item.precio_venta_momento:
                            item.precio_venta_momento = item.articulo.precio_venta
                        item.save()
                        total_venta += item.cantidad * item.precio_venta_momento
                    
                    venta.total = total_venta
                    # Validar que los montos coincidan con el total
                    total_pagado = venta.monto_efectivo + venta.monto_transferencia
                    if total_pagado != total_venta:
                        # Opcional: ajustar si uno es cero, o lanzar error. 
                        # Por ahora permitimos guardar pero es mejor que coincida.
                        pass
                    venta.save()

                    # Create cash movements based on payment amounts
                    if venta.monto_efectivo > 0:
                        MovimientoCaja.objects.create(
                            caja=caja_abierta,
                            usuario=request.user,
                            tipo='ingreso',
                            metodo_pago='efectivo',
                            monto=venta.monto_efectivo,
                            descripcion=f"Venta Buffet #{venta.id} (Efectivo)",
                            venta=venta
                        )
                    if venta.monto_transferencia > 0:
                        MovimientoCaja.objects.create(
                            caja=caja_abierta,
                            usuario=request.user,
                            tipo='ingreso',
                            metodo_pago='banco',
                            monto=venta.monto_transferencia,
                            descripcion=f"Venta Buffet #{venta.id} (Transferencia)",
                            venta=venta
                        )
                    
                    messages.success(request, f"Venta #{venta.id} registrada correctamente.")
                    return redirect('registrar_venta')
            except Exception as e:
                messages.error(request, f"Error al registrar la venta: {str(e)}")
    else:
        form = VentaForm(initial={'caja': caja_abierta, 'usuario': request.user})
        formset = ItemVentaFormSet(queryset=ItemVenta.objects.none())

    context = {
        'form': form,
        'formset': formset,
        'caja_abierta': caja_abierta,
        'sede': sede
    }
    return render(request, 'core/registrar_venta.html', context)

@login_required
def registrar_compra(request):
    try:
        sede = request.user.userprofile.sede
        if not sede:
            raise UserProfile.DoesNotExist
    except UserProfile.DoesNotExist:
        messages.error(request, "Tu usuario no está asociado a ninguna sede.")
        return redirect('admin:index')

    caja_abierta = Caja.objects.filter(sede=sede, tipo='BUFET', abierta=True).first()

    if request.method == 'POST':
        if not caja_abierta:
            messages.error(request, "Debe abrir una caja de buffet para registrar compras.")
            return redirect('registrar_compra')

        form = CompraForm(request.POST)
        formset = ItemCompraFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    compra = form.save(commit=False)
                    compra.usuario = request.user
                    compra.save()
                    
                    items = formset.save(commit=False)
                    total_compra = 0
                    for item in items:
                        item.compra = compra
                        item.save()
                        total_compra += item.cantidad * item.precio_costo_momento
                    
                    compra.total = total_compra
                    compra.save()
                    
                    messages.success(request, f"Compra #{compra.id} registrada correctamente.")
                    return redirect('registrar_compra')
            except Exception as e:
                messages.error(request, f"Error al registrar la compra: {str(e)}")
    else:
        form = CompraForm(initial={'usuario': request.user})
        formset = ItemCompraFormSet(queryset=ItemCompra.objects.none())

    context = {
        'form': form,
        'formset': formset,
        'caja_abierta': caja_abierta,
        'sede': sede,
    }
    return render(request, 'core/registrar_compra.html', context)

@login_required
def buscar_articulos(request):
    query = request.GET.get('q', '')
    context = request.GET.get('context', 'venta')  # 'venta' o 'compra'
    try:
        sede = request.user.userprofile.sede
    except UserProfile.DoesNotExist:
        return JsonResponse({'results': []}, status=400)

    articulos = Articulo.objects.filter(
        Q(descripcion__icontains=query) & Q(sede=sede)
    )[:10]

    if context == 'compra':
        # Asumimos que el modelo Articulo tiene un campo 'precio_costo'
        results = [{'id': a.id, 'text': a.descripcion, 'precio': a.precio_costo} for a in articulos]
    else:  # Por defecto, para 'venta'
        results = [{'id': a.id, 'text': a.descripcion, 'precio': a.precio_venta} for a in articulos]

    return JsonResponse({'results': results})



# --- Vistas de Caja ---

@login_required
def abrir_caja(request):
    tipo = request.GET.get('tipo', 'CANCHA')
    sede_id = request.GET.get('sede')
    next_url = request.GET.get('next', 'turno_grid')

    if request.method == 'POST':
        monto_inicial = request.POST.get('monto_inicial')
        sede_id_post = request.POST.get('sede')
        tipo_post = request.POST.get('tipo')
        next_url_post = request.POST.get('next', 'turno_grid')

        if monto_inicial and sede_id_post and tipo_post:
            sede = get_object_or_404(Sede, id=sede_id_post)
            if not Caja.objects.filter(sede=sede, fecha=timezone.now().date(), abierta=True, tipo=tipo_post).exists():
                Caja.objects.create(
                    sede=sede,
                    fecha=timezone.now().date(),
                    usuario_apertura=request.user,
                    monto_inicial=Decimal(monto_inicial),
                    abierta=True,
                    tipo=tipo_post
                )
                messages.success(request, f"Caja de tipo '{tipo_post}' abierta correctamente.")
            else:
                messages.warning(request, f"Ya existe una caja de tipo '{tipo_post}' abierta para hoy.")
            return redirect(next_url_post)

    sedes = Sede.objects.all()
    selected_sede = get_object_or_404(Sede, id=sede_id) if sede_id else (sedes.first() if sedes.exists() else None)

    context = {
        'sedes': sedes,
        'selected_sede': selected_sede,
        'tipo_caja': tipo,
        'next_url': next_url
    }
    return render(request, 'core/abrir_caja.html', context)

@login_required
def cerrar_caja(request):
    today = timezone.now().date()

    sede_id = request.GET.get('sede')
    tipo = request.GET.get('tipo')
    next_url = request.GET.get('next', 'turno_grid')

    # Sede and tipo are required to identify the correct cash box
    if not sede_id or not tipo:
        messages.error(request, "Se requiere Sede y Tipo para identificar la caja a cerrar.")
        return redirect(next_url)

    try:
        caja = Caja.objects.get(fecha=today, abierta=True, sede_id=sede_id, tipo=tipo)
    except Caja.DoesNotExist:
        messages.warning(request, f"No hay una caja de tipo '{tipo}' abierta para hoy en la sede seleccionada.")
        return redirect(next_url)

    if request.method == 'POST':
        monto_final_real = request.POST.get('monto_final_real')
        next_url_post = request.POST.get('next', 'turno_grid')
        if monto_final_real:
            caja.monto_final_real = Decimal(monto_final_real)
            ingresos_efectivo = MovimientoCaja.objects.filter(caja=caja, tipo='ingreso', metodo_pago='efectivo').aggregate(total=Sum('monto'))['total'] or Decimal('0.00')
            egresos_efectivo = MovimientoCaja.objects.filter(caja=caja, tipo='egreso', metodo_pago='efectivo').aggregate(total=Sum('monto'))['total'] or Decimal('0.00')
            monto_final_teorico = caja.monto_inicial + ingresos_efectivo - egresos_efectivo
            caja.monto_final_teorico = monto_final_teorico
            diferencia = caja.monto_final_real - monto_final_teorico
            caja.diferencia = diferencia
            caja.usuario_cierre = request.user
            caja.abierta = False
            caja.save()
            if diferencia != 0:
                admins = User.objects.filter(groups__name='Administrador')
                for admin in admins:
                    Notificacion.objects.create(
                        usuario=admin,
                        mensaje=f"Se registró una diferencia de ${diferencia} en la caja del día {today} en la sede {caja.sede.nombre}."
                    )
            messages.success(request, f"Caja de tipo '{tipo}' cerrada correctamente.")
            return redirect(next_url_post)

    ingresos_efectivo = MovimientoCaja.objects.filter(caja=caja, tipo='ingreso', metodo_pago='efectivo').aggregate(total=Sum('monto'))['total'] or Decimal('0.00')
    egresos_efectivo = MovimientoCaja.objects.filter(caja=caja, tipo='egreso', metodo_pago='efectivo').aggregate(total=Sum('monto'))['total'] or Decimal('0.00')
    monto_final_teorico = caja.monto_inicial + ingresos_efectivo - egresos_efectivo
    context = {'caja': caja, 'monto_final_teorico': monto_final_teorico, 'next_url': next_url}
    return render(request, 'core/cerrar_caja.html', context)