from django.urls import path

from .views import *


urlpatterns = [
    path('api/transactions-tables/create-order/',create_order),
    path('api/transactions-tables/update-order/<int:order_id>/',update_order),
    # path('api/transactions-tables/order-details/update/<int:id>/',update_order_detail),
    path('api/transactions-tables/create-payment/',create_payment),
    path('api/transactions-tables/order-details/<str:from_date>/<str:to_date>/',order_details_list),
    path('api/transactions-tables/order-summary/<str:from_date>/<str:to_date>/', order_summary_list),
]