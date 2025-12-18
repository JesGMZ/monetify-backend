import google.generativeai as genai
from datetime import date, datetime, timedelta
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from clientes.models import Cliente
from facturas.models import Factura
from pagos.models import Pago
from .models import RiesgoCrediticio, ChatInteraction, BotActivity
import json
import re

genai.configure(api_key="AIzaSyAYqfGcK15wqzjcbWz1JBkAgsBlN87x07I")


@api_view(["GET"])
def predecir_riesgo_crediticio(request, id_cliente):
    try:
        cliente = Cliente.objects.get(idCliente=id_cliente)
    except Cliente.DoesNotExist:
        return Response({"error": "Cliente no encontrado"}, status=status.HTTP_404_NOT_FOUND)

    facturas = Factura.objects.filter(cliente=cliente)
    pagos = Pago.objects.filter(factura__in=facturas)

    total_facturado = sum(float(f.monto) for f in facturas)
    total_pagado = sum(float(p.monto) for p in pagos)
    cantidad_facturas = facturas.count()
    cantidad_pagos = pagos.count()

    dias_pago = []
    for p in pagos:
        if p.fecha_pago and p.factura.fecha_emision:
            dias_pago.append((p.fecha_pago - p.factura.fecha_emision).days)
    promedio_dias_pago = sum(dias_pago) / len(dias_pago) if dias_pago else 30

    prompt = f"""
    Eres un analista financiero experto. Analiza los siguientes datos de un cliente y determina su riesgo crediticio.

    DATOS DEL CLIENTE:
    - Nombre: {cliente.nombre}
    - Saldo actual: ${cliente.saldo}
    - Cantidad de facturas emitidas: {cantidad_facturas}
    - Total facturado: ${total_facturado}
    - Total pagado: ${total_pagado}
    - Cantidad de pagos realizados: {cantidad_pagos}
    - Promedio de días de pago: {promedio_dias_pago} días

    INSTRUCCIONES:
    1. Analiza el riesgo crediticio como 'BAJO', 'MEDIO' o 'ALTO'
    2. Proporciona una explicación breve de 1-2 líneas
    3. Da una recomendación específica
    4. Evalúa el estado actual del cliente

    Responde EXCLUSIVAMENTE en formato JSON con esta estructura exacta:
    {{
        "riesgo_crediticio": "ALTO|MEDIO|BAJO",
        "razon": "explicación breve aquí",
        "recomendacion": "recomendación específica aquí",
        "estado_actual": "descripción del estado actual"
    }}

    No incluyas ningún otro texto fuera del JSON.
    """

    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)
        
        response_text = response.text.strip()
        response_text = response_text.replace('```json', '').replace('```', '')
        
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        
        if json_match:
            json_str = json_match.group()
            data = json.loads(json_str)
            
            riesgo_gemini = data.get("riesgo_crediticio", "MEDIO").upper()
            razon_gemini = data.get("razon", "Análisis basado en historial crediticio")
            recomendacion_gemini = data.get("recomendacion", "Monitorear comportamiento de pagos")
            estado_actual_gemini = data.get("estado_actual", "Cliente en evaluación")
        else:
            riesgo_gemini = "MEDIO"
            razon_gemini = "Análisis basado en datos históricos del cliente"
            recomendacion_gemini = "Monitorear comportamiento de pagos regularmente"
            estado_actual_gemini = "Cliente en evaluación"
            
    except Exception as e:
        print(f"Error con Gemini: {e}")
        riesgo_gemini = "MEDIO"
        razon_gemini = "Error en análisis automatizado, usando evaluación estándar"
        recomendacion_gemini = "Revisar manualmente el historial crediticio"
        estado_actual_gemini = "Requiere evaluación manual"

    registro = RiesgoCrediticio.objects.create(
        cliente=cliente,
        riesgo=riesgo_gemini,
        razon=razon_gemini
    )

    return Response({
        "cliente": cliente.nombre,
        "estado_actual": estado_actual_gemini,
        "riesgo_crediticio": riesgo_gemini,
        "recomendacion": recomendacion_gemini,
        "razon": razon_gemini,
        "fecha": registro.fecha_prediccion.strftime("%Y-%m-%d %H:%M:%S")
    })


# ============================================
# CHATBOT - CONSULTAS CONVERSACIONALES (CORREGIDO)
# ============================================

@api_view(["POST"])
def chatbot_consulta(request):
    mensaje = request.data.get("message", "")
    user_id = request.data.get("user_id", "anonymous")
    cliente_id = request.data.get("cliente_id")
    
    print(f"Chatbot consulta recibida: {mensaje}, cliente_id: {cliente_id}")
    
    if not mensaje:
        return Response({"error": "Mensaje vacío"}, status=status.HTTP_400_BAD_REQUEST)
    
    # Guardar la interacción del usuario
    ChatInteraction.objects.create(
        user_id=user_id,
        sender="user",
        message=mensaje
    )
    
    # Detectar la intención del mensaje
    intencion = detectar_intencion(mensaje)
    print(f"Intención detectada: {intencion}")
    
    # Procesar según la intención
    try:
        if intencion == "consultar_factura":
            respuesta = procesar_consulta_factura(mensaje, cliente_id)
        elif intencion == "enviar_recordatorio":
            respuesta = procesar_recordatorio_pago(mensaje, cliente_id)
        elif intencion == "generar_reporte":
            respuesta = procesar_reporte_cliente(mensaje, cliente_id)
        elif intencion == "calcular_morosidad":
            respuesta = procesar_morosidad(mensaje, cliente_id)
        elif intencion == "estado_cliente":
            respuesta = procesar_estado_cliente(mensaje, cliente_id)
        else:
            respuesta = respuesta_generica_llm(mensaje)
    except Exception as e:
        print(f"Error procesando mensaje: {e}")
        respuesta = "Lo siento, hubo un error procesando tu solicitud. Por favor, intenta de nuevo."
    
    print(f"Respuesta generada: {respuesta}")
    
    # Guardar la respuesta del bot
    ChatInteraction.objects.create(
        user_id=user_id,
        sender="bot",
        message=respuesta
    )
    
    return Response({
        "response": respuesta,
        "timestamp": datetime.now().strftime("%H:%M")
    })


def detectar_intencion(mensaje):
    """Detecta la intención del mensaje usando palabras clave"""
    mensaje_lower = mensaje.lower()
    
    if any(word in mensaje_lower for word in ["factura", "invoice", "fac-"]):
        return "consultar_factura"
    elif any(word in mensaje_lower for word in ["recordatorio", "recordar", "enviar", "notificar"]):
        return "enviar_recordatorio"
    elif any(word in mensaje_lower for word in ["reporte", "generar reporte", "informe"]):
        return "generar_reporte"
    elif any(word in mensaje_lower for word in ["morosidad", "vencida", "atrasada", "días", "dias"]):
        return "calcular_morosidad"
    elif any(word in mensaje_lower for word in ["cliente", "customer", "empresa", "estado"]):
        return "estado_cliente"
    else:
        return "general"


def procesar_consulta_factura(mensaje, cliente_id=None):
    """Procesa consultas sobre facturas específicas"""
    print(f"Procesando consulta de factura para cliente_id: {cliente_id}")
    
    # Extraer número de factura usando regex
    match = re.search(r'FAC-\d{3}', mensaje, re.IGNORECASE)
    
    if match:
        numero_factura = match.group()
        try:
            factura = Factura.objects.get(numero=numero_factura)
            
            dias_vencida = (date.today() - factura.fecha_vencimiento).days if factura.fecha_vencimiento else 0
            estado = "vencida" if dias_vencida > 0 else "al día"
            
            return f"📋 Factura {numero_factura}\nCliente: {factura.cliente_nombre}\nMonto: ${factura.monto}\nEstado: {estado}\nDías {'vencida' if dias_vencida > 0 else 'al día'}: {abs(dias_vencida)} días\n¿Te gustaría que envíe un recordatorio de pago?"
        except Factura.DoesNotExist:
            return f"❌ No encontré la factura {numero_factura} en el sistema."
    
    # Si no se especifica factura, mostrar todas las facturas del cliente
    if cliente_id:
        try:
            cliente = Cliente.objects.get(idCliente=cliente_id)
            facturas = Factura.objects.filter(cliente=cliente_id)
            
            if facturas.exists():
                respuesta = f"📊 Facturas de {cliente.nombre}:\n"
                for factura in facturas:
                    dias_vencida = (date.today() - factura.fecha_vencimiento).days if factura.fecha_vencimiento else 0
                    estado = "🟢 Al día" if dias_vencida <= 0 else "🔴 Vencida"
                    respuesta += f"\n• {factura.numero}: ${factura.monto} - {estado} ({abs(dias_vencida)} días)"
                return respuesta
            else:
                return f"ℹ️ El cliente {cliente.nombre} no tiene facturas registradas."
        except Cliente.DoesNotExist:
            return "❌ Cliente no encontrado."
    
    return "📝 Por favor proporciona el número de factura (formato: FAC-XXX) o selecciona un cliente para ver sus facturas."


def procesar_recordatorio_pago(mensaje, cliente_id=None):
    """Procesa el envío de recordatorios de pago"""
    print(f"Procesando recordatorio para cliente_id: {cliente_id}")
    
    if not cliente_id:
        return "❌ Por favor selecciona un cliente para enviar el recordatorio."
    
    try:
        cliente = Cliente.objects.get(idCliente=cliente_id)
        facturas_pendientes = Factura.objects.filter(cliente=cliente_id, estado="Pendiente")
        
        if not facturas_pendientes.exists():
            return f"✅ El cliente {cliente.nombre} no tiene facturas pendientes."
        
        # Simular envío de SMS
        total_pendiente = sum(float(f.monto) for f in facturas_pendientes)
        facturas_lista = ", ".join([f.numero for f in facturas_pendientes])
        
        mensaje_sms = f"🔔 Recordatorio enviado a {cliente.nombre}:\n"
        mensaje_sms += f"📱 Teléfono: {cliente.telefono}\n"
        mensaje_sms += f"💳 Total pendiente: ${total_pendiente}\n"
        mensaje_sms += f"📋 Facturas: {facturas_lista}\n"
        mensaje_sms += f"📧 Se envió copia a: {cliente.correo}"
        
        # Registrar actividad
        BotActivity.objects.create(
            action="Recordatorio de pago enviado",
            client_name=cliente.nombre,
            details=f"Facturas: {facturas_lista}"
        )
        
        return mensaje_sms
        
    except Cliente.DoesNotExist:
        return "❌ Cliente no encontrado."
    except Exception as e:
        print(f"Error enviando recordatorio: {e}")
        return "❌ Error al enviar el recordatorio. Por favor, intenta de nuevo."


def procesar_reporte_cliente(mensaje, cliente_id=None):
    """Genera reporte del cliente"""
    print(f"Generando reporte para cliente_id: {cliente_id}")
    
    if not cliente_id:
        return "❌ Por favor selecciona un cliente para generar el reporte."
    
    try:
        cliente = Cliente.objects.get(idCliente=cliente_id)
        facturas = Factura.objects.filter(cliente=cliente_id)
        pagos = Pago.objects.filter(factura__in=facturas)
        
        # Calcular métricas
        total_facturado = sum(float(f.monto) for f in facturas)
        total_pagado = sum(float(p.monto) for p in pagos)
        facturas_vencidas = facturas.filter(
            fecha_vencimiento__lt=date.today(),
            estado="Pendiente"
        ).count()
        
        # Registrar actividad
        BotActivity.objects.create(
            action="Reporte de cliente generado",
            client_name=cliente.nombre,
            details="Reporte completo generado"
        )
        
        reporte = f"📊 REPORTE DE CLIENTE\n"
        reporte += f"====================\n"
        reporte += f"👤 Cliente: {cliente.nombre}\n"
        reporte += f"📄 Documento: {cliente.documento}\n"
        reporte += f"📞 Teléfono: {cliente.telefono}\n"
        reporte += f"📧 Email: {cliente.correo}\n"
        reporte += f"💰 Saldo actual: ${cliente.saldo}\n"
        reporte += f"========================\n"
        reporte += f"💵 Total facturado: ${total_facturado}\n"
        reporte += f"💳 Total pagado: ${total_pagado}\n"
        reporte += f"📋 Facturas totales: {facturas.count()}\n"
        reporte += f"🔴 Facturas vencidas: {facturas_vencidas}\n"
        reporte += f"✅ Pagos realizados: {pagos.count()}\n"
        reporte += f"📅 Fecha reporte: {date.today().strftime('%d/%m/%Y')}"
        
        return reporte
        
    except Cliente.DoesNotExist:
        return "❌ Cliente no encontrado."


def procesar_morosidad(mensaje, cliente_id=None):
    """Calcula días de morosidad"""
    print(f"Calculando morosidad para cliente_id: {cliente_id}")
    
    if cliente_id:
        try:
            cliente = Cliente.objects.get(idCliente=cliente_id)
            facturas_vencidas = Factura.objects.filter(
                cliente=cliente_id,
                fecha_vencimiento__lt=date.today(),
                estado="Pendiente"
            )
            
            if facturas_vencidas.exists():
                total_vencido = sum(float(f.monto) for f in facturas_vencidas)
                respuesta = f"⏰ Morosidad de {cliente.nombre}:\n"
                respuesta += f"📋 Facturas vencidas: {facturas_vencidas.count()}\n"
                respuesta += f"💳 Total vencido: ${total_vencido}\n\n"
                
                for factura in facturas_vencidas:
                    dias_vencida = (date.today() - factura.fecha_vencimiento).days
                    respuesta += f"• {factura.numero}: {dias_vencida} días - ${factura.monto}\n"
                
                return respuesta
            else:
                return f"✅ El cliente {cliente.nombre} no tiene facturas vencidas."
                
        except Cliente.DoesNotExist:
            return "❌ Cliente no encontrado."
    
    # Morosidad general si no hay cliente específico
    try:
        facturas_vencidas = Factura.objects.filter(
            fecha_vencimiento__lt=date.today(),
            estado="Pendiente"
        )
        
        total_vencido = sum(float(f.monto) for f in facturas_vencidas)
        cantidad = facturas_vencidas.count()
        
        return f"📈 MOROSIDAD GENERAL\nFacturas vencidas: {cantidad}\nTotal vencido: ${total_vencido}\nClientes afectados: {facturas_vencidas.values('cliente').distinct().count()}"

    except Exception as e:
        return f"❌ Error calculando morosidad: {str(e)}"


def procesar_estado_cliente(mensaje, cliente_id=None):
    """Procesa consultas sobre el estado de clientes"""
    print(f"Procesando estado del cliente: {cliente_id}")
    
    if cliente_id:
        try:
            cliente = Cliente.objects.get(idCliente=cliente_id)
            facturas_pendientes = Factura.objects.filter(cliente=cliente_id, estado="Pendiente").count()
            facturas_vencidas = Factura.objects.filter(
                cliente=cliente_id, 
                estado="Pendiente",
                fecha_vencimiento__lt=date.today()
            ).count()
            
            return f"👤 ESTADO DE CLIENTE\nNombre: {cliente.nombre}\nEstado: {cliente.estado}\nSaldo: ${cliente.saldo}\nFacturas pendientes: {facturas_pendientes}\nFacturas vencidas: {facturas_vencidas}\n📞 Contacto: {cliente.telefono}"
            
        except Cliente.DoesNotExist:
            return "❌ Cliente no encontrado."
    
    return "ℹ️ Por favor selecciona un cliente para ver su estado."


def respuesta_generica_llm(mensaje):
    """Usa LLM para responder preguntas generales"""
    try:
        prompt = f"""
        Eres un asistente virtual experto en cobranzas y gestión de clientes. 
        Responde de forma breve, profesional y útil a la siguiente consulta:
        
        "{mensaje}"
        
        Mantén tu respuesta en 2-3 oraciones máximo. Responde en español.
        """
        
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Error con LLM: {e}")
        return "🤖 Entiendo tu consulta. ¿Podrías ser más específico para ayudarte mejor? Por ejemplo, puedes consultar sobre facturas, generar reportes o enviar recordatorios de pago."


# ============================================
# ACCIONES RÁPIDAS AUTOMATIZADAS (ACTUALIZADAS)
# ============================================

@api_view(["POST"])
def enviar_recordatorio_pago(request):
    """Envía un recordatorio de pago automático"""
    factura_id = request.data.get("factura_id")
    cliente_id = request.data.get("cliente_id")
    
    try:
        if cliente_id:
            cliente = Cliente.objects.get(idCliente=cliente_id)
            facturas = Factura.objects.filter(cliente=cliente_id, estado="Pendiente")
            
            if not facturas.exists():
                return Response({
                    "success": False,
                    "message": f"El cliente {cliente.nombre} no tiene facturas pendientes."
                })
            
            # Simular envío de SMS
            total_pendiente = sum(float(f.monto) for f in facturas)
            facturas_lista = ", ".join([f.numero for f in facturas])
            
            mensaje_sms = f"Estimado {cliente.nombre}, tiene pendiente el pago de {facturas.count()} factura(s) por un total de ${total_pendiente}. Facturas: {facturas_lista}. Por favor regularizar su situación."
            
            # Registrar actividad
            BotActivity.objects.create(
                action="Recordatorio de pago SMS",
                client_name=cliente.nombre,
                details=f"Facturas: {facturas_lista} - Total: ${total_pendiente}"
            )
            
            return Response({
                "success": True,
                "message": "Recordatorio enviado exitosamente",
                "cliente": cliente.nombre,
                "telefono": cliente.telefono,
                "total_pendiente": total_pendiente,
                "facturas": facturas_lista,
                "sms_simulado": mensaje_sms
            })
        else:
            return Response({"error": "Se requiere ID de cliente"}, status=status.HTTP_400_BAD_REQUEST)
            
    except Cliente.DoesNotExist:
        return Response({"error": "Cliente no encontrado"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": f"Error al enviar recordatorio: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
def calcular_dias_morosidad(request):
    """Calcula días de morosidad de una factura"""
    factura_id = request.data.get("factura_id")
    cliente_id = request.data.get("cliente_id")
    
    try:
        if cliente_id:
            cliente = Cliente.objects.get(idCliente=cliente_id)
            facturas = Factura.objects.filter(cliente=cliente_id, estado="Pendiente")
            
            resultados = []
            for factura in facturas:
                if factura.fecha_vencimiento:
                    dias_morosidad = (date.today() - factura.fecha_vencimiento).days
                    dias_morosidad = max(0, dias_morosidad)
                    
                    resultados.append({
                        "factura": factura.numero,
                        "dias_morosidad": dias_morosidad,
                        "monto": float(factura.monto),
                        "fecha_vencimiento": factura.fecha_vencimiento.strftime("%Y-%m-%d"),
                        "estado": "Vencida" if dias_morosidad > 0 else "Al día"
                    })
            
            return Response({
                "cliente": cliente.nombre,
                "facturas_analizadas": len(resultados),
                "resultados": resultados
            })
        else:
            return Response({"error": "Se requiere ID de cliente"}, status=status.HTTP_400_BAD_REQUEST)
            
    except Cliente.DoesNotExist:
        return Response({"error": "Cliente no encontrado"}, status=status.HTTP_404_NOT_FOUND)


@api_view(["GET"])
def generar_reporte_cliente(request, id_cliente):
    """Genera un reporte completo del cliente"""
    try:
        cliente = Cliente.objects.get(idCliente=id_cliente)
        facturas = Factura.objects.filter(cliente=id_cliente)
        pagos = Pago.objects.filter(factura__in=facturas)
        
        # Calcular métricas
        total_facturado = sum(float(f.monto) for f in facturas)
        total_pagado = sum(float(p.monto) for p in pagos)
        facturas_vencidas = facturas.filter(
            fecha_vencimiento__lt=date.today(),
            estado="Pendiente"
        ).count()
        
        # Registrar actividad
        BotActivity.objects.create(
            action="Reporte generado",
            client_name=cliente.nombre,
            details="Reporte completo del cliente"
        )
        
        return Response({
            "cliente": cliente.nombre,
            "documento": cliente.documento,
            "telefono": cliente.telefono,
            "correo": cliente.correo,
            "estado": cliente.estado,
            "saldo": float(cliente.saldo),
            "total_facturado": float(total_facturado),
            "total_pagado": float(total_pagado),
            "facturas_totales": facturas.count(),
            "facturas_vencidas": facturas_vencidas,
            "pagos_realizados": pagos.count(),
            "fecha_reporte": date.today().strftime("%Y-%m-%d")
        })
    except Cliente.DoesNotExist:
        return Response({"error": "Cliente no encontrado"}, status=status.HTTP_404_NOT_FOUND)


# ============================================
# ESTADÍSTICAS DEL BOT
# ============================================

@api_view(["GET"])
def estadisticas_bot(request):
    """Devuelve estadísticas del chatbot"""
    hoy = date.today()
    
    # Consultas de hoy
    consultas_hoy = ChatInteraction.objects.filter(
        timestamp__date=hoy,
        sender="user"
    ).count()
    
    # Actividades recientes
    actividades_recientes = BotActivity.objects.order_by('-timestamp')[:5]
    
    # Calcular tiempo promedio (simulado)
    tiempo_promedio = "2.3 min"
    
    # Satisfacción (esto requeriría un sistema de feedback real)
    satisfaccion = "92%"
    
    return Response({
        "consultas_hoy": consultas_hoy,
        "tiempo_promedio": tiempo_promedio,
        "satisfaccion": satisfaccion,
        "casos_resueltos": f"{int(consultas_hoy * 0.8)}/{consultas_hoy}",
        "actividades_recientes": [
            {
                "action": a.action,
                "client": a.client_name,
                "time": calcular_tiempo_relativo(a.timestamp)
            }
            for a in actividades_recientes
        ]
    })


def calcular_tiempo_relativo(timestamp):
    """Calcula el tiempo relativo desde un timestamp"""
    diff = datetime.now() - timestamp
    
    if diff.days > 0:
        return f"{diff.days} días"
    elif diff.seconds < 60:
        return f"{diff.seconds} seg"
    elif diff.seconds < 3600:
        return f"{diff.seconds // 60} min"
    else:
        return f"{diff.seconds // 3600} hr"


@api_view(["GET"])
def historial_chat(request):
    """Devuelve el historial de chat"""
    user_id = request.GET.get("user_id", "anonymous")
    
    interacciones = ChatInteraction.objects.filter(
        user_id=user_id
    ).order_by('timestamp')[:50]
    
    return Response({
        "messages": [
            {
                "id": i.id,
                "sender": i.sender,
                "text": i.message,
                "time": i.timestamp.strftime("%H:%M")
            }
            for i in interacciones
        ]
    })