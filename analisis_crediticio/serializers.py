from rest_framework import serializers
from .models import RiesgoCrediticio

class RiesgoCrediticioSerializer(serializers.ModelSerializer):
    class Meta:
        model = RiesgoCrediticio
        fields = "__all__"