from django.urls import path
from .views import *
urlpatterns = [

#User Master Table-----------------------------------------------
    path('api/customer/login/', customer_login),
    path('api/admin/login/', admin_login),
    path('api/user-master-table/all-users/', get_users),
    path('api/user-master-table/add-user/', add_user),
    path('api/user-master-table/user/<int:id>/',get_single_user),
    path('api/user-master-table/update-user/<int:id>/',update_user),
    path('api/user-master-table/user-status/<int:id>/',update_user_status),

#Product Master Table------------------------------------------------------
    path('api/product-master-table/all-products/', get_products),
    path('api/product-master-table/add-product/', add_product),
    path('api/product-master-table/product/<int:id>/', get_single_product),
    path('api/product-master-table/update-product/<int:id>/', update_product),
    path('api/product-master-table/product-status/<int:id>/',update_product_status),  
    path('api/product-master-table/import-products/',import_products),
    
#Payment Mode Master Table-----------------------------------------------------
    path('api/payment-mode-master-table/all-payment-modes/', get_payment_modes),
    path('api/payment-mode-master-table/add-payment-mode/', add_payment_mode),
    path('api/payment-mode-master-table/payment-mode/<int:id>/',get_single_payment_mode),
    path('api/payment-mode-master-table/update-payment-mode/<int:id>/',update_payment_mode),
    path('api/payment-mode-master-table/payment-mode-status/<int:id>/',update_payment_mode_status),
]