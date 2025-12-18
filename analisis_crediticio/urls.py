from django.urls import path
from . import views

urlpatterns = [
    # ============================================
    # ANÁLISIS CREDITICIO
    # ============================================
    path("predecir/<int:id_cliente>/", views.predecir_riesgo_crediticio, name="predecir_riesgo"),
    
    # ============================================
    # CHATBOT - CONSULTAS CONVERSACIONALES
    # ============================================
    path("chatbot/consulta/", views.chatbot_consulta, name="chatbot_consulta"),
    path("chatbot/historial/", views.historial_chat, name="historial_chat"),
    
    # ============================================
    # ACCIONES RÁPIDAS AUTOMATIZADAS
    # ============================================
    path("accion/enviar-recordatorio/", views.enviar_recordatorio_pago, name="enviar_recordatorio"),
    path("accion/calcular-morosidad/", views.calcular_dias_morosidad, name="calcular_morosidad"),
    path("accion/reporte-cliente/<int:id_cliente>/", views.generar_reporte_cliente, name="reporte_cliente"),
    
    # ============================================
    # ESTADÍSTICAS DEL BOT
    # ============================================
    path("bot/estadisticas/", views.estadisticas_bot, name="estadisticas_bot"),
]