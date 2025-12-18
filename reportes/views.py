from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db.models import Sum, Count, Q
from datetime import datetime, timedelta
import calendar

from .serializers import (
    ReporteEstadisticasSerializer,
    GraficoIngresosDeudasSerializer,
    GraficoEfectividadSerializer
)
from facturas.models import Factura
from pagos.models import Pago
from clientes.models import Cliente

def calcular_variacion(actual, anterior):
    if anterior == 0:
        return 100.0 if actual > 0 else 0.0
    return ((actual - anterior) / anterior) * 100

@api_view(['GET'])
def reporte_estadisticas(request):
    try:
        start_date_str = request.GET.get('start_date', '01/01/2024')
        end_date_str = request.GET.get('end_date', '30/06/2024')
        
        start_date = datetime.strptime(start_date_str, '%d/%m/%Y').date()
        end_date = datetime.strptime(end_date_str, '%d/%m/%Y').date()
        
        # Calcular período anterior para comparaciones
        periodo_dias = (end_date - start_date).days
        start_date_anterior = start_date - timedelta(days=periodo_dias)
        end_date_anterior = start_date - timedelta(days=1)
        
        print(f"Período actual: {start_date} a {end_date}")
        print(f"Período anterior: {start_date_anterior} a {end_date_anterior}")
        
        # INGRESOS TOTALES (pagos activos en el período)
        ingresos_totales = Pago.objects.filter(
            estado='Activo',  # Cambiado de 'CONFIRMADO' a 'Active'
            fecha_pago__range=[start_date, end_date]
        ).aggregate(total=Sum('monto'))['total'] or 0
        
        ingresos_anterior = Pago.objects.filter(
            estado='Activo',  # Cambiado de 'CONFIRMADO' a 'Active'
            fecha_pago__range=[start_date_anterior, end_date_anterior]
        ).aggregate(total=Sum('monto'))['total'] or 0
        
        ingresos_variacion = calcular_variacion(ingresos_totales, ingresos_anterior)
        
        print(f"Ingresos totales: {ingresos_totales}")
        print(f"Ingresos anteriores: {ingresos_anterior}")
        
        # DEUDAS PENDIENTES (facturas pendientes + vencidas)
        deudas_pendientes = Factura.objects.filter(
            estado__in=['Pendiente', 'Vencida']  # Estados correctos
        ).aggregate(total=Sum('monto'))['total'] or 0
        
        deudas_anterior = Factura.objects.filter(
            estado__in=['Pendiente', 'Vencida'],
            fecha_emision__lte=end_date_anterior
        ).aggregate(total=Sum('monto'))['total'] or 0
        
        deudas_variacion = calcular_variacion(deudas_pendientes, deudas_anterior)
        
        print(f"Deudas pendientes: {deudas_pendientes}")
        print(f"Deudas anteriores: {deudas_anterior}")
        
        # EFECTIVIDAD DE COBRANZA
        # Total facturas emitidas (todas las facturas existentes)
        total_facturas = Factura.objects.count()
        
        # Facturas pagadas (total o parcialmente con pagos activos)
        facturas_pagadas = Factura.objects.filter(
            Q(estado='Pagada') | 
            Q(pagos__estado='Activo')  # Cambiado de 'CONFIRMADO' a 'Active'
        ).distinct().count()
        
        efectividad_cobranza = (facturas_pagadas / total_facturas * 100) if total_facturas > 0 else 0
        
        # Para el período anterior (simplificado)
        total_facturas_anterior = Factura.objects.filter(
            fecha_emision__lte=end_date_anterior
        ).count()
        
        facturas_pagadas_anterior = Factura.objects.filter(
            Q(estado='Pagada') | 
            Q(pagos__estado='Activo'),  # Cambiado de 'CONFIRMADO' a 'Active'
            fecha_emision__lte=end_date_anterior
        ).distinct().count()
        
        efectividad_anterior = (facturas_pagadas_anterior / total_facturas_anterior * 100) if total_facturas_anterior > 0 else 0
        efectividad_variacion = calcular_variacion(efectividad_cobranza, efectividad_anterior)
        
        print(f"Total facturas: {total_facturas}")
        print(f"Facturas pagadas: {facturas_pagadas}")
        print(f"Efectividad: {efectividad_cobranza}%")
        
        # CLIENTES ACTIVOS
        clientes_activos = Cliente.objects.filter(estado='Activo').count()
        
        # Nuevos clientes en el período (simplificado)
        nuevos_clientes = Cliente.objects.count()  # Temporal
        
        data = {
            'ingresos_totales': float(ingresos_totales),
            'deudas_pendientes': float(deudas_pendientes),
            'efectividad_cobranza': round(efectividad_cobranza, 2),
            'clientes_activos': clientes_activos,
            'ingresos_variacion': round(ingresos_variacion, 2),
            'deudas_variacion': round(deudas_variacion, 2),
            'efectividad_variacion': round(efectividad_variacion, 2),
            'nuevos_clientes': nuevos_clientes,
        }
        
        print("Datos finales:", data)
        
        serializer = ReporteEstadisticasSerializer(data)
        return Response(serializer.data)
        
    except Exception as e:
        print(f"Error en reporte_estadisticas: {str(e)}")
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_400_BAD_REQUEST
        )

@api_view(['GET'])
def grafico_ingresos_deudas(request):
    """
    Endpoint para datos del gráfico de barras (Ingresos vs Deudas mensuales)
    """
    try:
        start_date_str = request.GET.get('start_date', '01/01/2024')
        end_date_str = request.GET.get('end_date', '30/06/2024')
        
        start_date = datetime.strptime(start_date_str, '%d/%m/%Y').date()
        end_date = datetime.strptime(end_date_str, '%d/%m/%Y').date()
        
        data = []
        current_date = start_date.replace(day=1)  # Empezar desde el primer día del mes
        
        # Generar datos mensuales
        while current_date <= end_date:
            month_start = current_date
            if current_date.month == 12:
                month_end = current_date.replace(year=current_date.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                month_end = current_date.replace(month=current_date.month + 1, day=1) - timedelta(days=1)
            
            if month_end > end_date:
                month_end = end_date
            
            # Ingresos del mes (pagos activos)
            ingresos_mes = Pago.objects.filter(
                estado='Activo',  # Cambiado de 'CONFIRMADO' a 'Active'
                fecha_pago__range=[month_start, month_end]
            ).aggregate(total=Sum('monto'))['total'] or 0
            
            # Deudas del mes (facturas pendientes/vencidas al final del mes)
            deudas_mes = Factura.objects.filter(
                estado__in=['Pendiente', 'Vencida'],  # Estados correctos
                fecha_emision__lte=month_end
            ).aggregate(total=Sum('monto'))['total'] or 0
            
            data.append({
                'name': calendar.month_abbr[month_start.month],
                'ingresos': float(ingresos_mes),
                'deudas': float(deudas_mes)
            })
            
            # Avanzar al siguiente mes
            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year + 1, month=1, day=1)
            else:
                current_date = current_date.replace(month=current_date.month + 1, day=1)
        
        serializer = GraficoIngresosDeudasSerializer(data, many=True)
        return Response(serializer.data)
        
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_400_BAD_REQUEST
        )

@api_view(['GET'])
def grafico_efectividad(request):
    """
    Endpoint para datos del gráfico de línea (Efectividad de cobranza mensual)
    """
    try:
        start_date_str = request.GET.get('start_date', '01/01/2024')
        end_date_str = request.GET.get('end_date', '30/06/2024')
        
        start_date = datetime.strptime(start_date_str, '%d/%m/%Y').date()
        end_date = datetime.strptime(end_date_str, '%d/%m/%Y').date()
        
        data = []
        current_date = start_date.replace(day=1)  # Empezar desde el primer día del mes
        
        while current_date <= end_date:
            month_start = current_date
            if current_date.month == 12:
                month_end = current_date.replace(year=current_date.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                month_end = current_date.replace(month=current_date.month + 1, day=1) - timedelta(days=1)
            
            if month_end > end_date:
                month_end = end_date
            
            # Facturas emitidas en el mes
            facturas_mes = Factura.objects.filter(
                fecha_emision__range=[month_start, month_end]
            )
            total_facturas = facturas_mes.count()
            
            # Facturas pagadas (total o parcialmente con pagos activos)
            facturas_pagadas = facturas_mes.filter(
                Q(estado='Pagada') | 
                Q(pagos__estado='Activo')  # Cambiado de 'CONFIRMADO' a 'Active'
            ).distinct().count()
            
            efectividad = (facturas_pagadas / total_facturas * 100) if total_facturas > 0 else 0
            
            data.append({
                'name': calendar.month_abbr[month_start.month],
                'efectividad': round(efectividad, 2)
            })
            
            # Avanzar al siguiente mes
            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year + 1, month=1, day=1)
            else:
                current_date = current_date.replace(month=current_date.month + 1, day=1)
        
        serializer = GraficoEfectividadSerializer(data, many=True)
        return Response(serializer.data)
        
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_400_BAD_REQUEST
        )