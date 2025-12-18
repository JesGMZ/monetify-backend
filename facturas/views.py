from rest_framework import viewsets, filters
from .models import Factura
from .serializers import FacturaSerializer
from clientes.models import Cliente
from datetime import date

class FacturaViewSet(viewsets.ModelViewSet):
    queryset = Factura.objects.all().order_by('-fecha_emision')
    serializer_class = FacturaSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['numero', 'cliente__nombre', 'estado']
    ordering_fields = ['fecha_emision', 'monto']

    def perform_create(self, serializer):
        ultimo_numero = Factura.objects.count() + 1
        numero_factura = f"FAC-{ultimo_numero:03d}" 

        factura = serializer.save(
            numero=numero_factura,
            estado="Pendiente"
        )

        cliente = factura.cliente

        cliente.saldo -= factura.monto
        cliente.save()

        total_pagos = sum(p.monto for p in factura.pagos.all())

        if total_pagos >= factura.monto:
            factura.estado = "Pagada"
        elif factura.fecha_vencimiento and factura.fecha_vencimiento < date.today():
            factura.estado = "Vencida"
        else:
            factura.estado = "Pendiente"

        factura.save()
