from rest_framework import serializers
from .models import *


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserMaster
        fields = ['id', 'username', 'name', 'account_type', 'active_status']


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductMaster
        fields = '__all__'

class PaymentModeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentModeMaster
        fields = '__all__'