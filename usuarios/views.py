from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from rest_framework import status
from django.contrib.auth.models import User
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from .models import UserProfile
from .serializers import RegisterSerializer

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer

class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        profile, created = UserProfile.objects.get_or_create(user=user)
        
        # Valores por defecto para notificaciones si no existen
        default_notifications = {
            'facturas': True,
            'confirmacionPagos': True,
            'smsCobranza': False,
            'alertasVencimiento': True,
            'reportesDiarios': True
        }
        
        # Valores por defecto para configuración del sistema
        default_system = {
            'diasAlertaVencimiento': 7
        }
        
        return Response({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "telefono": profile.telefono or "",
            "cargo": profile.cargo or "Usuario del Sistema",
            "notificaciones": profile.notificaciones or default_notifications,
            "configuracion_sistema": profile.configuracion_sistema or default_system
        })

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_profile(request):
    """Actualizar perfil del usuario con modelo extendido"""
    try:
        user = request.user
        user.first_name = request.data.get('first_name', user.first_name)
        user.last_name = request.data.get('last_name', user.last_name)
        user.email = request.data.get('email', user.email)
        user.save()
        
        # Actualizar perfil extendido
        profile, created = UserProfile.objects.get_or_create(user=user)
        profile.telefono = request.data.get('telefono', profile.telefono)
        profile.cargo = request.data.get('cargo', profile.cargo)
        profile.save()
        
        return Response({
            'message': 'Perfil actualizado exitosamente',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'telefono': profile.telefono,
                'cargo': profile.cargo,
            }
        })
    except Exception as e:
        return Response(
            {'error': f'Error al actualizar el perfil: {str(e)}'}, 
            status=status.HTTP_400_BAD_REQUEST
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    """Cambiar contraseña del usuario"""
    try:
        # Validar que las contraseñas coincidan
        new_password = request.data.get('new_password')
        confirm_password = request.data.get('confirm_password')
        
        if new_password != confirm_password:
            return Response(
                {'error': 'Las contraseñas no coinciden'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validar longitud mínima
        if len(new_password) < 6:
            return Response(
                {'error': 'La contraseña debe tener al menos 6 caracteres'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Usar PasswordChangeForm para validar la contraseña actual
        form_data = {
            'old_password': request.data.get('current_password'),
            'new_password1': new_password,
            'new_password2': confirm_password
        }
        
        form = PasswordChangeForm(user=request.user, data=form_data)
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, form.user)
            return Response({'message': 'Contraseña cambiada exitosamente'})
        else:
            errors = {}
            for field, error_list in form.errors.items():
                if field == 'old_password':
                    errors['current_password'] = error_list
                elif field == 'new_password2':
                    errors['confirm_password'] = error_list
                else:
                    errors[field] = error_list
            return Response(
                {'errors': errors}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    except Exception as e:
        return Response(
            {'error': f'Error al cambiar la contraseña: {str(e)}'}, 
            status=status.HTTP_400_BAD_REQUEST
        )

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_preferences(request):
    """Actualizar preferencias del usuario con modelo extendido"""
    try:
        user = request.user
        profile, created = UserProfile.objects.get_or_create(user=user)
        
        # Actualizar notificaciones si vienen en el request
        if 'notificaciones' in request.data:
            profile.notificaciones = request.data['notificaciones']
        
        # Actualizar configuración del sistema si viene en el request
        if 'sistema' in request.data:
            profile.configuracion_sistema = request.data['sistema']
        
        profile.save()
        
        return Response({
            'message': 'Preferencias actualizadas exitosamente',
            'preferences': {
                'notificaciones': profile.notificaciones,
                'sistema': profile.configuracion_sistema
            }
        })
    except Exception as e:
        return Response(
            {'error': f'Error al actualizar preferencias: {str(e)}'}, 
            status=status.HTTP_400_BAD_REQUEST
        )