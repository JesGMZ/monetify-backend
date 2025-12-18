from django.db import models
from clientes.models import Cliente

class Factura(models.Model):
    ESTADOS = [
        ("Pagada", "Pagada"),
        ("Pendiente", "Pendiente"),
        ("Vencida", "Vencida"),
    ]

    idFactura = models.AutoField(primary_key=True)
    numero = models.CharField(max_length=20, unique=True)  
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name="facturas")
    fecha_emision = models.DateField()
    fecha_vencimiento = models.DateField()
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    estado = models.CharField(max_length=20, choices=ESTADOS, default="Pendiente")

    def __str__(self):
        return f"{self.numero} - {self.cliente.nombre}"
