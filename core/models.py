from django.db import models, transaction
from django.contrib.auth.models import User
from django.dispatch import receiver
from django.db.models.signals import post_save, m2m_changed
from decimal import Decimal

class Sede(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    direccion = models.CharField(max_length=255)
    
    def __str__(self):
        return self.nombre

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    sede = models.ForeignKey(Sede, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.user.username

class Cancha(models.Model):
    sede = models.ForeignKey(Sede, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=100)
    
    def __str__(self):
        return f"{self.nombre} ({self.sede.nombre})"

class Cliente(models.Model):
    nombre = models.CharField(max_length=150)
    telefono = models.CharField(max_length=50, null=True, blank=True)
    observaciones = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.nombre} - {self.telefono if self.telefono else 'Sin Teléfono'}"

class Turno(models.Model):
    ESTADOS = [('libre', 'Libre'), ('ocupado', 'Ocupado')]
    
    cancha = models.ForeignKey(Cancha, on_delete=models.CASCADE)
    cliente = models.ForeignKey(Cliente, on_delete=models.SET_NULL, null=True, blank=True)
    fecha_hora_inicio = models.DateTimeField()
    fecha_hora_fin = models.DateTimeField()
    estado = models.CharField(max_length=10, choices=ESTADOS, default='libre')
    
    precio_total = models.DecimalField(max_digits=10, decimal_places=2)
    monto_efectivo = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    monto_transferencia = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    monto_senia = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Solo para turnos especiales que requieren seña.")
    
    observaciones = models.TextField(blank=True)

    def __str__(self):
        return f"Turno en {self.cancha} - {self.fecha_hora_inicio.strftime('%d/%m %H:%M')}"

    def save(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().save(*args, **kwargs)
        
        if self.estado == 'ocupado' and user:
            try:
                caja = Caja.objects.get(sede=self.cancha.sede, fecha=self.fecha_hora_inicio.date(), abierta=True, tipo='CANCHA')
                
                if self.monto_efectivo > 0:
                    MovimientoCaja.objects.update_or_create(
                        turno=self,
                        metodo_pago='efectivo',
                        defaults={
                            'caja': caja,
                            'usuario': user,
                            'tipo': 'ingreso',
                            'monto': self.monto_efectivo,
                            'descripcion': f"Cobro de turno: {self}",
                        }
                    )
                
                if self.monto_transferencia > 0:
                    MovimientoCaja.objects.update_or_create(
                        turno=self,
                        metodo_pago='banco',
                        defaults={
                            'caja': caja,
                            'usuario': user,
                            'tipo': 'ingreso',
                            'monto': self.monto_transferencia,
                            'descripcion': f"Cobro de turno (transferencia): {self}",
                        }
                    )
            except Caja.DoesNotExist:
                pass

class Caja(models.Model):
    TIPOS = [('CANCHA', 'Cancha'), ('BUFET', 'Bufet')]
    sede = models.ForeignKey(Sede, on_delete=models.CASCADE)
    fecha = models.DateField()
    tipo = models.CharField(max_length=10, choices=TIPOS, default='CANCHA')
    usuario_apertura = models.ForeignKey(User, related_name='cajas_abiertas', on_delete=models.PROTECT)
    monto_inicial = models.DecimalField(max_digits=10, decimal_places=2)
    
    usuario_cierre = models.ForeignKey(User, related_name='cajas_cerradas', on_delete=models.PROTECT, null=True, blank=True)
    monto_final_teorico = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    monto_final_real = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    diferencia = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    abierta = models.BooleanField(default=True)

    class Meta:
        unique_together = ('fecha', 'sede', 'tipo')

    def __str__(self):
        return f"Caja {self.get_tipo_display()} de {self.sede.nombre} - {self.fecha}"

class MovimientoCaja(models.Model):
    TIPO_MOVIMIENTO = [('ingreso', 'Ingreso'), ('egreso', 'Egreso')]
    METODO_PAGO = [('efectivo', 'Efectivo'), ('banco', 'Banco/Transferencia')]

    caja = models.ForeignKey(Caja, on_delete=models.PROTECT)
    usuario = models.ForeignKey(User, on_delete=models.PROTECT)
    tipo = models.CharField(max_length=10, choices=TIPO_MOVIMIENTO)
    metodo_pago = models.CharField(max_length=20, choices=METODO_PAGO)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    descripcion = models.CharField(max_length=255)
    
    turno = models.ForeignKey(Turno, on_delete=models.CASCADE, null=True, blank=True)
    venta = models.ForeignKey('Venta', on_delete=models.SET_NULL, null=True, blank=True)
    compra = models.ForeignKey('Compra', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.get_tipo_display()} de ${self.monto} ({self.get_metodo_pago_display()})"

class ClientePublicidad(models.Model):
    empresa = models.CharField(max_length=150, unique=True)
    contacto_nombre = models.CharField(max_length=100)
    contacto_telefono = models.CharField(max_length=50)

    def __str__(self):
        return self.empresa

class ContratoPublicidad(models.Model):
    cliente = models.ForeignKey(ClientePublicidad, on_delete=models.CASCADE)
    monto_acordado = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_inicio = models.DateField()
    fecha_vencimiento = models.DateField()

    def __str__(self):
        return f"Contrato con {self.cliente.empresa}"

class Notificacion(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    mensaje = models.TextField()
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    leida = models.BooleanField(default=False)

    def __str__(self):
        return f"Notificación para {self.usuario.username}: {self.mensaje[:30]}"

class Configuracion(models.Model):
    precio_turno = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        verbose_name = "Configuración"
        verbose_name_plural = "Configuraciones"

    def __str__(self):
        return "Configuración General"

class Articulo(models.Model):
    descripcion = models.CharField(max_length=255)
    precio_costo = models.DecimalField(max_digits=10, decimal_places=2)
    precio_venta = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField(default=0, help_text="Stock actual. Se actualiza automáticamente con ventas y compras.")
    stock_minimo = models.PositiveIntegerField(default=0)
    sede = models.ForeignKey(Sede, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('descripcion', 'sede')

    def __str__(self):
        return self.descripcion

class Proveedor(models.Model):
    nombre = models.CharField(max_length=200, unique=True)

    def __str__(self):
        return self.nombre

class Venta(models.Model):
    caja = models.ForeignKey(Caja, on_delete=models.PROTECT, limit_choices_to={'tipo': 'BUFET', 'abierta': True})
    fecha = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(User, on_delete=models.PROTECT)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    monto_efectivo = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    monto_transferencia = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    articulos = models.ManyToManyField(Articulo, through='ItemVenta')

class ItemVenta(models.Model):
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE)
    articulo = models.ForeignKey(Articulo, on_delete=models.PROTECT)
    cantidad = models.PositiveIntegerField(default=1)
    precio_venta_momento = models.DecimalField(max_digits=10, decimal_places=2, help_text="Precio al momento de la venta")

    def save(self, *args, **kwargs):
        if not self.pk:
            with transaction.atomic():
                self.articulo.stock -= self.cantidad
                self.articulo.save()
        super().save(*args, **kwargs)

class Compra(models.Model):
    proveedor = models.ForeignKey(Proveedor, on_delete=models.PROTECT)
    fecha = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(User, on_delete=models.PROTECT)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    gastos_varios = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Gastos adicionales que suman al total (ej: flete).")
    bonificaciones = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Descuentos o bonificaciones que restan del total.")
    articulos = models.ManyToManyField(Articulo, through='ItemCompra')

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

class ItemCompra(models.Model):
    compra = models.ForeignKey(Compra, on_delete=models.CASCADE)
    articulo = models.ForeignKey(Articulo, on_delete=models.PROTECT)
    cantidad = models.PositiveIntegerField(default=1)
    precio_costo_momento = models.DecimalField(max_digits=10, decimal_places=2, help_text="Costo al momento de la compra")

    def save(self, *args, **kwargs):
        if not self.pk:
            with transaction.atomic():
                self.articulo.stock += self.cantidad
                self.articulo.save()
        super().save(*args, **kwargs)

@receiver(m2m_changed, sender=Venta.articulos.through)
def update_venta_total(sender, instance, action, **kwargs):
    if action in ['post_add', 'post_remove', 'post_clear']:
        total = sum(item.cantidad * item.precio_venta_momento for item in instance.itemventa_set.all())
        Venta.objects.filter(pk=instance.pk).update(total=total)

@receiver(m2m_changed, sender=Compra.articulos.through)
def update_compra_total(sender, instance, action, **kwargs):
    if action in ['post_add', 'post_remove', 'post_clear']:
        subtotal = sum(item.cantidad * item.precio_costo_momento for item in instance.itemcompra_set.all())
        total = subtotal + (instance.gastos_varios or Decimal('0')) - (instance.bonificaciones or Decimal('0'))
        Compra.objects.filter(pk=instance.pk).update(total=total)

@receiver(post_save, sender=Compra)
def update_compra_total_on_save(sender, instance, **kwargs):
    subtotal = sum(item.cantidad * item.precio_costo_momento for item in instance.itemcompra_set.all())
    total = subtotal + (instance.gastos_varios or Decimal('0')) - (instance.bonificaciones or Decimal('0'))
    if instance.total != total:
        Compra.objects.filter(pk=instance.pk).update(total=total)