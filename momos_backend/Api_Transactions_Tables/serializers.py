from rest_framework import serializers
from .models import OrderSummary,OrderDetails

class OrderDetailsSerializer(serializers.ModelSerializer):
    date = serializers.DateField(format="%d-%m-%Y")
    class Meta:
        model = OrderDetails
        fields = '__all__'

class OrderSummarySerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(source='created_by.first_name', read_only=True)
    date = serializers.DateField(format="%d-%m-%Y")
    class Meta:
        model = OrderSummary
        fields = '__all__'