from rest_framework import serializers
from .models import Factura

class FacturaSerializer(serializers.ModelSerializer):
    cliente_nombre = serializers.CharField(source="cliente.nombre", read_only=True)

    class Meta:
        model = Factura
        fields = "__all__"
        extra_kwargs = {
            'numero': {'required': False},  
            'estado': {'required': False}
        }