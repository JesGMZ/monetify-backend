# riesgos/models.py
from django.db import models
from clientes.models import Cliente

class RiesgoCrediticio(models.Model):
    NIVELES = [
        ("BAJO", "Bajo"),
        ("MEDIO", "Medio"),
        ("ALTO", "Alto"),
    ]

    idRiesgo = models.AutoField(primary_key=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name="riesgos")
    riesgo = models.CharField(max_length=20, choices=NIVELES)
    razon = models.TextField()
    fecha_prediccion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'riesgo_crediticio'
        verbose_name = 'Riesgo Crediticio'
        verbose_name_plural = 'Riesgos Crediticios'
        ordering = ['-fecha_prediccion']

    def __str__(self):
        return f"{self.cliente.nombre} - {self.riesgo}"


class ChatInteraction(models.Model):
    """Almacena las interacciones del chatbot con los usuarios"""
    SENDER_CHOICES = [
        ('user', 'Usuario'),
        ('bot', 'Bot'),
    ]
    
    idInteraccion = models.AutoField(primary_key=True)
    user_id = models.CharField(max_length=100, default="anonymous", db_index=True)
    sender = models.CharField(max_length=10, choices=SENDER_CHOICES)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        db_table = 'chat_interactions'
        ordering = ['timestamp']
        verbose_name = 'Interacción de Chat'
        verbose_name_plural = 'Interacciones de Chat'
        indexes = [
            models.Index(fields=['user_id', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.get_sender_display()} - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"


class BotActivity(models.Model):
    """Registra las actividades y acciones realizadas por el bot"""
    ACTION_TYPES = [
        ('recordatorio', 'Recordatorio enviado'),
        ('consulta', 'Consulta atendida'),
        ('reporte', 'Reporte generado'),
        ('calculo', 'Cálculo realizado'),
        ('otro', 'Otra acción'),
    ]
    
    idActividad = models.AutoField(primary_key=True)
    action_type = models.CharField(max_length=20, choices=ACTION_TYPES, default='otro')
    action = models.CharField(max_length=100)
    client_name = models.CharField(max_length=200)
    details = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        db_table = 'bot_activities'
        ordering = ['-timestamp']
        verbose_name = 'Actividad del Bot'
        verbose_name_plural = 'Actividades del Bot'
        indexes = [
            models.Index(fields=['timestamp']),
            models.Index(fields=['action_type', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.action} - {self.client_name} ({self.timestamp.strftime('%Y-%m-%d %H:%M')})"