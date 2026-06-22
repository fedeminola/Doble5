from django import forms
from .models import Venta, ItemVenta, Compra, ItemCompra, Articulo, Proveedor

class VentaForm(forms.ModelForm):
    class Meta:
        model = Venta
        fields = ['caja', 'usuario', 'monto_efectivo', 'monto_transferencia']
        widgets = {
            'caja': forms.HiddenInput(),
            'usuario': forms.HiddenInput(),
            'monto_efectivo': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'monto_transferencia': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

class ItemVentaForm(forms.ModelForm):
    class Meta:
        model = ItemVenta
        fields = ['articulo', 'cantidad', 'precio_venta_momento']
        widgets = {
            'articulo': forms.Select(attrs={'class': 'form-select articulo-select'}),
            'cantidad': forms.NumberInput(attrs={'class': 'form-control cantidad-input', 'min': '1'}),
            'precio_venta_momento': forms.NumberInput(attrs={'class': 'form-control precio-input', 'step': '0.01'}),
        }

ItemVentaFormSet = forms.inlineformset_factory(
    Venta, ItemVenta, form=ItemVentaForm,
    extra=1, can_delete=True, can_delete_extra=True
)

class CompraForm(forms.ModelForm):
    class Meta:
        model = Compra
        fields = ['proveedor', 'usuario', 'gastos_varios', 'bonificaciones']
        widgets = {
            'proveedor': forms.Select(attrs={'class': 'form-select'}),
            'usuario': forms.HiddenInput(),
            'gastos_varios': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'bonificaciones': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

class ItemCompraForm(forms.ModelForm):
    class Meta:
        model = ItemCompra
        fields = ['articulo', 'cantidad', 'precio_costo_momento']
        widgets = {
            'articulo': forms.Select(attrs={'class': 'form-select articulo-select'}),
            'cantidad': forms.NumberInput(attrs={'class': 'form-control cantidad-input', 'min': '1'}),
            'precio_costo_momento': forms.NumberInput(attrs={'class': 'form-control costo-input', 'step': '0.01'}),
        }

ItemCompraFormSet = forms.inlineformset_factory(
    Compra, ItemCompra, form=ItemCompraForm,
    extra=1, can_delete=True, can_delete_extra=True
)