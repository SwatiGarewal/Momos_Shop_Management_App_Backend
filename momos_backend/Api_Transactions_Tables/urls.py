from django.urls import path

from .views import create_order,create_payment


urlpatterns = [
    path('api/transactions-tables/create-order/',create_order),
    path('api/transactions-tables/create-payment/',create_payment),
]