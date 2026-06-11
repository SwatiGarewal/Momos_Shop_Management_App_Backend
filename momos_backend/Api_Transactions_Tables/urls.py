from django.urls import path

from .views import *


urlpatterns = [
    path('api/transactions-tables/create-order/',create_order),
    path('api/transactions-tables/create-payment/',create_payment),
    path('api/transactions-tables/order-details/',order_details_list),
    path('api/transactions-tables/order-summary/', order_summary_list),
]