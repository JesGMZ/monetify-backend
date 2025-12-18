from rest_framework import viewsets, filters
from .models import Pago
from .serializers import PagoSerializer
from facturas.models import Factura
from clientes.models import Cliente
from datetime import date

class PagoViewSet(viewsets.ModelViewSet):
    queryset = Pago.objects.all().order_by('-fecha_pago')
    serializer_class = PagoSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['factura__numero', 'factura__cliente__nombre', 'estado']
    ordering_fields = ['fecha_pago', 'monto']

    def perform_create(self, serializer):
        pago = serializer.save(estado="Activo")

        factura = pago.factura
        cliente = factura.cliente

        if pago.estado == "Activo":
            cliente.saldo += pago.monto
            cliente.save()

        pagos_total = sum(p.monto for p in factura.pagos.filter(estado="Activo"))

        if pagos_total >= factura.monto:
            factura.estado = "Pagada"
        elif factura.fecha_vencimiento and factura.fecha_vencimiento < date.today():
            factura.estado = "Vencida"
        else:
            factura.estado = "Pendiente"

        factura.save()

    def perform_destroy(self, instance):
        factura = instance.factura
        cliente = factura.cliente

        if instance.estado == "Activo":
            cliente.saldo -= instance.monto
            cliente.save()

        instance.estado = "Inactivo"
        instance.save()

        pagos_total = sum(p.monto for p in factura.pagos.filter(estado="Activo"))

        from datetime import date
        if pagos_total >= factura.monto:
            factura.estado = "Pagada"
        elif factura.fecha_vencimiento and factura.fecha_vencimiento < date.today():
            factura.estado = "Vencida"
        else:
            factura.estado = "Pendiente"

        factura.save()
