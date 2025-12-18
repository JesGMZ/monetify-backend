# proyecto/urls.py
from django.contrib import admin
from django.urls import path, include
from rest_framework import routers
from clientes.views import ClienteViewSet
from pagos.views import PagoViewSet
from facturas.views import FacturaViewSet
from analisis_crediticio.views import predecir_riesgo_crediticio

router = routers.DefaultRouter()
router.register(r'clientes', ClienteViewSet)
router.register(r'pagos', PagoViewSet)
router.register(r'facturas', FacturaViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/riesgos/predecir/<int:id_cliente>/', predecir_riesgo_crediticio, name='predecir_riesgo'),
    path('api/analisis_crediticio/', include('analisis_crediticio.urls')),
    path('api/reportes/', include('reportes.urls')),
    path('api/auth/', include('usuarios.urls')),
]
