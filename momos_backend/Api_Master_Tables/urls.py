from django.urls import path
from .views import *
urlpatterns = [
    path('api/product-master-table/all-products/', get_products),
    path('api/product-master-table/add-product/', add_product),
    path('api/product-master-table/product/<int:id>/', get_single_product),
    path('api/product-master-table/update-product/<int:id>/', update_product),
    path('api/product-master-table/deactivate-product/<int:id>/', deactivate_product),
    path('api/product-master-table/activate-product/<int:id>/', activate_product),
    path('api/user-master-table/all-users/', get_users),
    path('api/user-master-table/add-user/', add_user),
    path('api/user-master-table/login-user/', login_user),
    path('api/payment-mode-master-table/all-payment-modes/', get_payment_modes),
    path('api/payment-mode-master-table/add-payment-mode/', add_payment_mode),
]