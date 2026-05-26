from rest_framework import serializers
from .models import ProductMaster

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductMaster
        fields = '__all__'