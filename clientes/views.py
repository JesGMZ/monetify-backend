from rest_framework import viewsets, filters
from .models import Cliente
from .serializers import ClienteSerializer

class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.all().order_by('idCliente')
    serializer_class = ClienteSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]

    search_fields = ['nombre', 'documento', 'estado']

    ordering_fields = ['nombre', 'saldo']
