from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views

urlpatterns = [
    # Autenticación JWT
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Perfil de usuario
    path('profile/', views.UserProfileView.as_view(), name='user_profile'),
    path('profile/update/', views.update_profile, name='update_profile'),
    
    # Seguridad
    path('change-password/', views.change_password, name='change_password'),
    
    # Preferencias
    path('preferences/', views.update_preferences, name='update_preferences'),
]
