# pagos/models.py
from django.db import models
from facturas.models import Factura

class Pago(models.Model):
    idPago = models.AutoField(primary_key=True)
    factura = models.ForeignKey(Factura, on_delete=models.CASCADE, related_name="pagos")
    fecha_pago = models.DateField()
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    metodo_pago = models.CharField(
        max_length=50,
        choices=[("EFECTIVO", "Efectivo"), ("TRANSFERENCIA", "Transferencia"), ("TARJETA", "Tarjeta")],
        default="EFECTIVO"
    )
    estado = models.CharField(
        max_length=20,
        choices=[("PENDIENTE", "Pendiente"), ("CONFIRMADO", "Confirmado"), ("ANULADO", "Anulado")],
        default="CONFIRMADO"
    )

    def __str__(self):
        return f"Pago {self.idPago} - Factura {self.factura.idFactura}"
