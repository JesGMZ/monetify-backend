from django.db import models

class Cliente(models.Model):
    ESTADOS = [
        ("Activo", "Activo"),
        ("Moroso", "Moroso"),
        ("En Riesgo", "En Riesgo"),
    ]

    idCliente = models.AutoField(primary_key=True)
    nombre = models.CharField("Nombre o Razón Social", max_length=150)
    documento = models.CharField("RUC", max_length=20, unique=True)
    telefono = models.CharField("Teléfono", max_length=20, blank=True, null=True)
    correo = models.EmailField("Correo electrónico", blank=True, null=True)
    estado = models.CharField("Estado", max_length=20, choices=ESTADOS, default="Activo")
    saldo = models.DecimalField("Saldo", max_digits=12, decimal_places=2, default=0)

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre
