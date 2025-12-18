from rest_framework import serializers

class ReporteEstadisticasSerializer(serializers.Serializer):
    ingresos_totales = serializers.DecimalField(max_digits=15, decimal_places=2)
    deudas_pendientes = serializers.DecimalField(max_digits=15, decimal_places=2)
    efectividad_cobranza = serializers.DecimalField(max_digits=5, decimal_places=2)
    clientes_activos = serializers.IntegerField()
    ingresos_variacion = serializers.DecimalField(max_digits=5, decimal_places=2)
    deudas_variacion = serializers.DecimalField(max_digits=5, decimal_places=2)
    efectividad_variacion = serializers.DecimalField(max_digits=5, decimal_places=2)
    nuevos_clientes = serializers.IntegerField()

class GraficoIngresosDeudasSerializer(serializers.Serializer):
    name = serializers.CharField()
    ingresos = serializers.DecimalField(max_digits=12, decimal_places=2)
    deudas = serializers.DecimalField(max_digits=12, decimal_places=2)

class GraficoEfectividadSerializer(serializers.Serializer):
    name = serializers.CharField()
    efectividad = serializers.DecimalField(max_digits=5, decimal_places=2)